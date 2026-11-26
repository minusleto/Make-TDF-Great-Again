#!/usr/bin/env python3
"""Static QA for the TDF Aral Sea mechanic.

Run from the repository root:
    python -I skills/aral-sea-mechanic/scripts/mech_audit.py mdredux --prefix aral
    python -I skills/aral-sea-mechanic/scripts/mech_audit.py mdredux --prefix aral --json reports/aral.json

Checks are based on available TDF source, curated MDC Wiki references in docs/aral-sea/,
and explicit Aral design invariants. Unknown identifiers are not attributed to another
mod; request the target TDF file when a required definition is undocumented.
"""
import argparse, collections, glob, json, os, re, sys

BANNED = ["strengthen ties", "mutual benefit", "significant", "foothold", "valuable",
          "comprehensive", "ensuring", "paving the way", "foster"]
CAPITALS = ["Moscow", "Beijing", "Astana", "Nur-Sultan", "Tashkent", "Ankara", "Tehran",
            "Washington", "Bishkek", "Dushanbe", "Москва", "Москв", "Пекин", "Ташкент",
            "Астан", "Анкар", "Тегеран", "Бишкек", "Душанбе"]
YEAR_RE = re.compile(r"\b(?:200\d|201\d|202[0-5])\b")
OUT = collections.defaultdict(list)
GENERIC_TREASURY_COST_KEYS = {
    "cost_0_5", "cost_1_0", "cost_1_5", "cost_3_0", "cost_4_0", "cost_4_5",
    "cost_7_5", "cost_8_0", "cost_10_0", "cost_25_0", "cost_40_0", "cost_50_0",
}


def add(sev, area, msg):
    OUT[sev].append((area, msg))


def rd(path):
    with open(path, "rb") as handle:
        b = handle.read()
    return b, b.decode("utf-8-sig", errors="replace").replace("\r", "")


def strip_comments(t):
    return re.sub(r"#[^\n]*", "", t)


def match_brace(t, i):
    """index of the brace that closes the one at t[i]"""
    d = 0
    for k in range(i, len(t)):
        c = t[k]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return k
    return -1


def blocks(t, depth=0):
    """name -> body for `name = {` blocks that start at the given brace depth"""
    res, d, i, n = {}, 0, 0, len(t)
    pat = re.compile(r"([A-Za-z0-9_.:@\-]+)\s*=\s*\{")
    while i < n:
        c = t[i]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
        else:
            m = pat.match(t, i) if (c.isalnum() or c == "_") and (i == 0 or not (t[i - 1].isalnum() or t[i - 1] in "_.")) else None
            if m and d == depth:
                j = m.end() - 1
                e = match_brace(t, j)
                if e < 0:
                    break
                res[m.group(1)] = t[j + 1:e]
                i = e + 1
                continue
        i += 1
    return res


def inner(t, name):
    m = re.search(r"\b" + re.escape(name) + r"\s*=\s*\{", t)
    if not m:
        return None
    e = match_brace(t, m.end() - 1)
    return t[m.end():e] if e > 0 else None


def custom_cost_blocked_key_issues(decisions, loc, langs):
    """Every custom_cost_text needs a language-specific _blocked key."""
    issues = []
    for decision, body in decisions.items():
        match = re.search(r"custom_cost_text\s*=\s*(\S+)", body)
        if not match:
            continue
        base = match.group(1)
        if base.startswith("cost_"):
            continue  # shared TDF generic treasury keys own their blocked variants
        blocked = base + "_blocked"
        for lang in langs:
            if blocked not in loc.get(lang, {}):
                issues.append(("decision " + decision, "blocked custom-cost key %s is missing (%s)" % (blocked, lang)))
    return issues


def implied_custom_cost_localisation_keys(decisions):
    """Return localisation keys used implicitly by custom_cost_text suffix conventions."""
    implied = set()
    for body in decisions.values():
        match = re.search(r"custom_cost_text\s*=\s*(\S+)", body)
        if match:
            base = match.group(1)
            if not base.startswith("cost_"):
                implied.add(base + "_blocked")
                implied.add(base + "_tooltip")
    return implied


def aral_pp_cost_label_issues(decision, body, localisations, languages):
    """The native decision UI displays cost = N; custom_cost_text displays treasury cash."""
    if re.search(r"(?m)^\s*cost\s*=\s*[0-9]+", body):
        return []
    cost = re.search(r"(?m)^\s*cost\s*=\s*([0-9]+)", body)
    label = re.search(r"custom_cost_text\s*=\s*(\S+)", body)
    if not cost or not label:
        return []
    issues = []
    for language in languages:
        value = localisations.get(language, {}).get(label.group(1), "")
        if not re.search(r"(?<!\d)" + cost.group(1) + r"(?!\d)", value):
            issues.append(("decision " + decision, "political-power cost %s is charged but not shown in label %s (%s): '%s'" % (cost.group(1), label.group(1), language, value)))
    return issues


def aral_decision_cost_issues(decisions):
    """Check category gating and keep political power on the native decision cost."""
    issues = []
    for decision, body in decisions.items():
        if re.search(r"(?m)^[ \t]*allowed[ \t]*=[ \t]*[{][^}]*original_tag[ \t]*=[ \t]*KAZ", body):
            issues.append(("decision " + decision, "remove duplicate KAZ allowed gate; the parent decision category already restricts the country"))
        if (
            re.search(r"add_political_power[ \t]*=[ \t]*-[0-9]+", body)
            or re.search(r"(?m)^[ \t]*ai_hint_pp_cost[ \t]*=", body)
            or re.search(r"has_political_power[ \t]*>", body)
        ):
            issues.append((
                "decision " + decision,
                "use the native decision cost = N for political power; remove ai_hint_pp_cost, has_political_power custom gating and manual PP debits",
            ))
    return issues

def aral_expected_cost_key(amount):
    return "cost_" + format(amount, ".1f").replace(".", "_")


def aral_treasury_cost_issues(decisions, events):
    """Aral cash costs are full treasury debits; the TDF economy finances negative balances."""
    issues = []
    for decision, body in decisions.items():
        area = "decision " + decision
        label = re.search(r"custom_cost_text\s*=\s*(\S+)", body)
        trigger = inner(body, "custom_cost_trigger")
        complete = inner(body, "complete_effect") or ""
        debits = re.findall(r"treasury_change\s*=\s*(-?[\d.]+)", complete)
        treasury_effects = re.findall(r"modify_treasury_effect\s*=\s*yes", complete)
        if not label:
            issues.append((area, "missing shared generic treasury cost_text key"))
        elif label.group(1) not in GENERIC_TREASURY_COST_KEYS:
            issues.append((area, "custom_cost_text %s is not a verified shared TDF treasury key" % label.group(1)))
        if trigger is not None:
            issues.append((area, "remove the redundant custom_cost_trigger; custom_cost_text displays the price without a treasury affordability gate"))
        if re.search(r"\btreasury\s*>", body):
            issues.append((area, "treasury-balance affordability gate blocks automatic debt financing"))
        if len(debits) != 1 or len(treasury_effects) != 1:
            issues.append((area, "charge the full project price with exactly one treasury_change and one modify_treasury_effect"))
        elif float(debits[0]) >= 0:
            issues.append((area, "project treasury_change must be a negative full cash cost"))
        elif label and label.group(1) != aral_expected_cost_key(abs(float(debits[0]))):
            issues.append((area, "generic price key %s does not match full treasury debit %s" % (label.group(1), abs(float(debits[0])))))
        if re.search(r"debt_change\s*=|modify_debt_effect\s*=\s*yes", body):
            issues.append((area, "explicit debt transaction duplicates the TDF automatic negative-treasury financing"))

    for event_id, body in events.items():
        if re.search(r"check_variable\s*=\s*\{\s*treasury\s*>", body):
            issues.append(("event " + event_id, "treasury-balance gate blocks a cash expense that should be financed automatically"))
        if re.search(r"debt_change\s*=|modify_debt_effect\s*=\s*yes", body):
            issues.append(("event " + event_id, "event expenses must use the treasury effect only; do not add debt separately"))
    return issues


def aral_localisation_style_issues(text):
    """The project omits the optional Paradox :0 localisation version suffix."""
    issues = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith(" ") and ':0 "' in line:
            issues.append(("localisation", "remove optional :0 version suffix at line %d" % line_number))
    return issues


def aral_modifier_issues(dyn, effects):
    """Require regional ecological effects and event-only national political spirits."""
    issues = []
    state = dyn.get("aral_state_modifier", "")
    if "aral_sea_dynamic_modifier" in dyn:
        issues.append(("dynamic modifiers", "remove the country-wide Aral ecological modifier; environmental fallout must remain state-scoped"))
    update = effects.get("update_aral_sea", "")
    if "aral_sea_dynamic_modifier" in update or re.search(r"\baral_mod_(?:agri|agtax|pop|migr|jobs)\b", update):
        issues.append(("scripted effect update_aral_sea", "country-wide ecological penalty attachment/calculations must not be present"))
    for key in ("state_productivity_growth_modifier", "local_building_slots_factor", "recruitable_population_factor"):
        if key not in state:
            issues.append(("dynamic modifier aral_state_modifier", "required Aral state modifier %s is missing" % key))
    for spirit_name in ("aral_regional_neglect_modifier", "aral_regional_crisis_modifier"):
        spirit = dyn.get(spirit_name, "")
        for key in ("stability_factor", "political_power_factor"):
            if key not in spirit:
                issues.append(("dynamic modifier " + spirit_name, "event-driven political spirit must define " + key))
    return issues


def aral_regional_crisis_issues(events, decisions, effects):
    """Check the warning, temporary neglect penalty, permanent crisis and recovery route."""
    issues = []
    tick = effects.get("aral_monthly_tick", "")
    warning = events.get("aral_sea.10", "")
    escalation = events.get("aral_sea.11", "")
    recovery = decisions.get("aral_regional_response", "")
    if not re.search(r"check_variable\s*=\s*\{\s*aral_deficit\s*>\s*69\.99\s*\}", tick):
        issues.append(("scripted effect aral_monthly_tick", "annual regional warning must require aral_deficit > 69.99"))
    for flag in ("aral_regional_warning_sent", "aral_regional_monitoring_done"):
        if not re.search(r"NOT\s*=\s*\{\s*has_country_flag\s*=\s*" + flag + r"\s*\}", tick):
            issues.append(("scripted effect aral_monthly_tick", "annual regional warning must be suppressed by " + flag))
    if not re.search(r"country_event\s*=\s*\{\s*id\s*=\s*aral_sea\.10\s+days\s*=\s*14\s*\}", tick):
        issues.append(("scripted effect aral_monthly_tick", "high regional deficit must fire warning event aral_sea.10"))
    if not re.search(r"add_dynamic_modifier\s*=\s*\{\s*modifier\s*=\s*aral_regional_neglect_modifier\s+days\s*=\s*730\s*\}", warning):
        issues.append(("event aral_sea.10", "postponing the response must add the 730-day temporary neglect spirit"))
    if not re.search(r"country_event\s*=\s*\{\s*id\s*=\s*aral_sea\.11\s+days\s*=\s*540\s*\}", warning):
        issues.append(("event aral_sea.10", "postponing the response must schedule the follow-up event after 540 days"))
    if not re.search(r"set_country_flag\s*=\s*aral_regional_monitoring_done", warning):
        issues.append(("event aral_sea.10", "funding regional monitoring must mark the programme complete"))
    followup_trigger = inner(escalation, "trigger") or ""
    if not re.search(r"has_country_flag\s*=\s*aral_regional_neglect_started", followup_trigger):
        issues.append(("event aral_sea.11", "follow-up event must require the pending neglect chain"))
    if not re.search(r"remove_dynamic_modifier\s*=\s*\{\s*modifier\s*=\s*aral_regional_neglect_modifier\s*\}", escalation):
        issues.append(("event aral_sea.11", "follow-up must remove the temporary neglect spirit"))
    if not re.search(r"add_dynamic_modifier\s*=\s*\{\s*modifier\s*=\s*aral_regional_crisis_modifier\s*\}", escalation):
        issues.append(("event aral_sea.11", "continued inaction must add the permanent regional crisis spirit"))
    visible = inner(recovery, "visible") or ""
    available = inner(recovery, "available") or ""
    complete = inner(recovery, "complete_effect") or ""
    remove = inner(recovery, "remove_effect") or ""
    if not re.search(r"has_country_flag\s*=\s*aral_regional_crisis", visible):
        issues.append(("decision aral_regional_response", "recovery decision must appear only during the permanent crisis"))
    if not re.search(r"controls_state\s*=\s*717", available):
        issues.append(("decision aral_regional_response", "recovery decision must require Kazakhstan to control state 717"))
    if not re.search(r"treasury_change\s*=\s*-1\.5", complete) or "modify_treasury_effect" not in complete or not re.search(r"cost\s*=\s*60", recovery):
        issues.append(("decision aral_regional_response", "recovery decision must charge 1.5 bn and 60 PP"))
    if not re.search(r"remove_dynamic_modifier\s*=\s*\{\s*modifier\s*=\s*aral_regional_crisis_modifier\s*\}", remove):
        issues.append(("decision aral_regional_response", "completed recovery decision must remove the permanent crisis spirit"))
    if not re.search(r"clr_country_flag\s*=\s*aral_regional_crisis", remove):
        issues.append(("decision aral_regional_response", "completed recovery decision must clear the crisis flag"))
    return issues


def aral_initialization_issues(effects):
    """Require save-safe initialization of every persistent variable read before its first write."""
    issues = []
    required = ("aral_sea_restoration", "aral_pending", "aral_relief", "aral_year_clock", "aral_gui_dirty")
    initializer = effects.get("aral_initialize_variables", "")
    for variable in required:
        guarded = re.search(
            r"NOT\s*=\s*\{\s*has_variable\s*=\s*" + re.escape(variable) +
            r"\s*\}\s*\}\s*set_variable\s*=\s*\{\s*" + re.escape(variable) + r"\s*=\s*0\s*\}",
            initializer,
        )
        if not guarded:
            issues.append(("scripted effect aral_initialize_variables", "must initialize missing country variable %s without resetting existing saves" % variable))
    for effect_name in ("update_aral_sea", "aral_monthly_tick"):
        body = effects.get(effect_name, "")
        if not re.match(r"\s*aral_initialize_variables\s*=\s*yes\b", body):
            issues.append(("scripted effect " + effect_name, "must call aral_initialize_variables before reading or updating Aral state"))
    return issues


def aral_ownership_issues(decisions, effects, code_all):
    """Enforce the Aral coast ownership gates and persistent state modifier contract."""
    issues = []
    for decision, body in decisions.items():
        available = inner(body, "available") or ""
        visible = inner(body, "visible") or ""
        decision_groups = {
            "aral_ifas": "program", "aral_loan": "program", "aral_dike": "program", "aral_saxaul1": "program",
            "aral_channel": "syrdarya", "aral_kokaral": "syrdarya", "aral_aklak": "syrdarya",
            "aral_irrigation": "agri", "aral_fish": "agri", "aral_saxaul2": "green",
            "aral_amanotkel": "phase2", "aral_phase2": "phase2", "aral_dam2": "phase2",
            "aral_uzb": "diplomacy", "aral_sibaral": "diplomacy",
            "aral_sib_canal": "diplomacy", "aral_sib_pipe": "diplomacy",
        }
        group = decision_groups.get(decision)
        if group is not None and not re.search(r"aral_unlocked_" + re.escape(group) + r"\s*=\s*yes", available):
            issues.append(("decision " + decision, "the correct Aral focus-group gate must be present in available"))
        if re.search(r"aral_unlocked_(?:program|syrdarya|agri|green|phase2|diplomacy)\s*=\s*yes", visible):
            issues.append(("decision " + decision, "focus-group gates must not hide the decision; put the gate in available"))
        if not re.search(r"\bcontrols_state\s*=\s*717\b", available):
            issues.append(("decision " + decision, "available must require controls_state = 717"))
        if re.search(r"\bowns_state\s*=\s*717\b", available):
            issues.append(("decision " + decision, "use controls_state = 717 for the decision gate, not owns_state"))
        if "aral_req_coast_tt" in available:
            issues.append(("decision " + decision, "remove the obsolete coast custom_trigger_tooltip; use plain controls_state = 717"))

    required_focuses = {
        "aral_unlocked_program": "KAZ_economy",
        "aral_unlocked_syrdarya": "KAZ_fight_capacity_deficit",
        "aral_unlocked_agri": "KAZ_ABP",
        "aral_unlocked_green": "KAZ_ecologization",
        "aral_unlocked_phase2": "KAZ_balance_north_and_south",
        "aral_unlocked_diplomacy": "KAZ_foreign_policy",
    }
    for trigger, focus in required_focuses.items():
        trigger_body = inner(code_all, trigger) or ""
        if not re.search(r"has_completed_focus\s*=\s*" + re.escape(focus) + r"\b", trigger_body):
            issues.append(("scripted trigger " + trigger, "must require completed focus " + focus))
        if re.search(r"\balways\s*=\s*yes\b", trigger_body):
            issues.append(("scripted trigger " + trigger, "must not be left permanently open"))

    monthly = inner(code_all, "on_monthly")
    if monthly is None or not re.search(r"original_tag\s*=\s*KAZ", monthly) or not re.search(r"owns_state\s*=\s*717", monthly):
        issues.append(("on_actions", "on_monthly must call the Aral tick only for KAZ while it owns state 717"))

    startup = inner(code_all, "on_startup")
    kaz_startup = inner(startup, "KAZ") if startup is not None else None
    if kaz_startup is None or not re.search(r"owns_state\s*=\s*717", kaz_startup) or not re.search(r"update_aral_sea\s*=\s*yes", kaz_startup):
        issues.append(("on_actions", "on_startup must scope into KAZ and initialize Aral only while it owns state 717"))

    update = effects.get("update_aral_sea", "")
    if not re.search(r"if\s*=\s*\{\s*limit\s*=\s*\{\s*owns_state\s*=\s*717\b", update):
        issues.append(("scripted_effect update_aral_sea", "recalculation must be gated by owns_state = 717"))

    monthly_tick = effects.get("aral_monthly_tick", "")
    if not re.search(r"if\s*=\s*\{\s*limit\s*=\s*\{\s*owns_state\s*=\s*717\b", monthly_tick):
        issues.append(("scripted_effect aral_monthly_tick", "monthly tick must be gated by owns_state = 717"))

    for decision, body in decisions.items():
        complete = inner(body, "complete_effect") or ""
        hidden = inner(complete, "hidden_effect") or ""
        if re.search(r"modify_(?:treasury|debt)_effect\s*=\s*yes", hidden):
            issues.append(("decision " + decision, "treasury/debt effects must be outside hidden_effect so their cost effects are visible"))
        if decision != "aral_sibaral" and not re.search(r"^\s*fire_only_once\s*=\s*yes\s*$", body, re.M):
            issues.append(("decision " + decision, "one-shot Aral projects must keep fire_only_once = yes"))
        if inner(body, "cancel_trigger") is not None or inner(body, "cancel_effect") is not None:
            issues.append(("decision " + decision, "Aral project decisions must not use ownership-based cancellation"))

    state_update = effects.get("aral_state_update", "")
    owned_update = inner(state_update, "if") or ""
    owned_limit = inner(owned_update, "limit") or ""
    if not re.search(r"is_owned_by\s*=\s*KAZ", owned_limit):
        issues.append(("scripted_effect aral_state_update", "state modifier values must recalculate only while the state is owned by KAZ"))
    for variable in ("aral_s_prod", "aral_s_slots", "aral_s_recruit"):
        assignment = r"set_variable\s*=\s*\{\s*" + re.escape(variable) + r"\s*=\s*KAZ\.aral_deficit\s*\}"
        if not re.search(assignment, owned_update):
            issues.append(("scripted_effect aral_state_update", variable + " must read KAZ.aral_deficit and be written in state scope"))
    add_position = owned_update.find("add_dynamic_modifier = { modifier = aral_state_modifier }")
    force_position = owned_update.find("force_update_dynamic_modifier = yes")
    variable_positions = [owned_update.find("set_variable = { " + variable) for variable in ("aral_s_prod", "aral_s_slots", "aral_s_recruit")]
    if add_position < 0:
        issues.append(("scripted_effect aral_state_update", "must add aral_state_modifier in state scope while KAZ owns the state"))
    elif any(position < 0 for position in variable_positions) or max(variable_positions) > add_position:
        issues.append(("scripted_effect aral_state_update", "state variables must be assigned before first attaching aral_state_modifier"))
    if force_position < 0 or (add_position >= 0 and force_position < add_position):
        issues.append(("scripted_effect aral_state_update", "must force-refresh the state dynamic modifier after assigning its variables"))
    if re.search(r"remove_dynamic_modifier\s*=\s*\{\s*modifier\s*=\s*aral_state_modifier\b", code_all):
        issues.append(("state modifier", "aral_state_modifier must remain on the state when ownership changes; do not remove it"))
    return issues


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="mdredux")
    ap.add_argument("--prefix", default="aral")
    ap.add_argument("--wiki", default="docs/aral-sea", help="curated MDC Wiki reference folder (default: docs/aral-sea)")
    ap.add_argument("--json")
    a = ap.parse_args()
    P = a.prefix.lower()
    root = a.root

    # ---------- discover files ----------
    files = []
    for sub in ["common", "events", "interface", "gfx", "localisation"]:
        for f in glob.glob(os.path.join(root, sub, "**", "*"), recursive=True):
            if os.path.isfile(f) and os.path.basename(f).lower().startswith(P):
                files.append(f)
    if not files:
        print("no files with prefix", P, "under", root)
        return 2
    code_files = [f for f in files if f.endswith((".txt", ".gui", ".gfx"))]
    loc_files = [f for f in files if f.endswith(".yml")]
    txt = {f: rd(f) for f in files}
    code_all = "\n".join(strip_comments(txt[f][1]) for f in code_files)

    # ---------- A. format ----------
    for f in files:
        b, t = txt[f]
        short = os.path.relpath(f, root)
        if f.endswith(".yml"):
            if not b.startswith(b"\xef\xbb\xbf"):
                add("ERROR", short, "yml without BOM")
            if P == "aral":
                for area, msg in aral_localisation_style_issues(t):
                    add("ERROR", short, msg)
        if f.endswith((".txt", ".gui", ".gfx", ".yml")):
            if b.count(b"\n") != b.count(b"\r\n"):
                add("ERROR", short, "bare LF line endings (repo uses CRLF)")
        if f.endswith((".txt", ".gui", ".gfx")):
            c = strip_comments(t)
            if c.count("{") != c.count("}"):
                add("ERROR", short, "brace mismatch %d/%d" % (c.count("{"), c.count("}")))
            sp = [i + 1 for i, l in enumerate(t.split("\n")) if re.match(r"^ +\S", l)]
            if sp:
                add("WARN", short, "space indentation on %d lines (first: %d)" % (len(sp), sp[0]))

    # ---------- B. localisation ----------
    loc = {}
    for f in loc_files:
        lang = "ru" if "russian" in f else ("en" if "english" in f else os.path.basename(os.path.dirname(f)))
        d = {}
        t = txt[f][1]
        for ln, l in enumerate(t.split("\n"), 1):
            m = re.match(r'^ ([A-Za-z0-9_.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$', l)
            if m:
                if m.group(1) in d:
                    add("ERROR", os.path.relpath(f, root), "duplicate loc key %s (line %d)" % (m.group(1), ln))
                d[m.group(1)] = m.group(2)
            elif l.strip() and not l.startswith(("l_", " #", "#")) and not l.strip().startswith("#"):
                add("WARN", os.path.relpath(f, root), "unparsed yml line %d: %s" % (ln, l[:60]))
        loc.setdefault(lang, {}).update(d)
    langs = sorted(loc)
    for x in langs:
        for y in langs:
            if x < y:
                for k in sorted(set(loc[x]) - set(loc[y])):
                    add("ERROR", "loc", "key %s present in %s but missing in %s" % (k, x, y))
                for k in sorted(set(loc[y]) - set(loc[x])):
                    add("ERROR", "loc", "key %s present in %s but missing in %s" % (k, y, x))
    L = loc.get("en") or (loc[langs[0]] if langs else {})

    # ---------- structure ----------
    dec_text = "\n".join(strip_comments(txt[f][1]) for f in code_files if "/decisions/" in f and "/categories/" not in f)
    cat_text = "\n".join(strip_comments(txt[f][1]) for f in code_files if "/categories/" in f)
    ev_text = "\n".join(strip_comments(txt[f][1]) for f in code_files if "/events/" in f)
    eff_text = "\n".join(strip_comments(txt[f][1]) for f in code_files if "/scripted_effects/" in f)
    trg_text = "\n".join(strip_comments(txt[f][1]) for f in code_files if "/scripted_triggers/" in f)
    dm_text = "\n".join(strip_comments(txt[f][1]) for f in code_files if "/dynamic_modifiers/" in f)
    sg_text = "\n".join(strip_comments(txt[f][1]) for f in code_files if "/scripted_guis/" in f)
    gui_text = "\n".join(txt[f][1] for f in code_files if f.endswith(".gui"))
    gfx_text = "\n".join(txt[f][1] for f in code_files if f.endswith(".gfx"))

    decisions = {}
    for cat, body in blocks(dec_text, 0).items():
        for n, b in blocks(body, 0).items():
            decisions[n] = b
    effects = blocks(eff_text, 0)
    triggers = blocks(trg_text, 0)
    dyn = blocks(dm_text, 0)
    events = {}
    depth, pos = 0, 0
    for m in re.finditer(r"\{|\}|\bcountry_event\s*=\s*\{", ev_text):
        tok = m.group(0)
        if tok == "}":
            depth -= 1
        elif tok == "{":
            depth += 1
        else:  # a definition only at depth 0: calls inside other events are not definitions
            if depth == 0:
                e = match_brace(ev_text, m.end() - 1)
                b = ev_text[m.end():e]
                i = re.search(r"\bid\s*=\s*(\S+)", b)
                if i:
                    events[i.group(1)] = b
            depth += 1

    # ---------- C. decisions ----------
    pp_re = re.compile(r"(?:PP|ПВ)\b")
    for n, b in decisions.items():
        area = "decision " + n
        cost = re.search(r"^\s*cost\s*=\s*(\d+)", b, re.M)
        cct = re.search(r"custom_cost_text\s*=\s*(\S+)", b)
        cce = inner(b, "complete_effect") or ""
        cre = inner(b, "remove_effect") or ""
        for k in (n, n + "_desc"):
            for lg in langs:
                if k not in loc[lg]:
                    add("ERROR", area, "loc key %s missing (%s)" % (k, lg))
        if "ai_will_do" not in b:
            add("WARN", area, "no ai_will_do")
        if not n.startswith(P + "_debug") and 'log = "' not in cce + cre:
            add("WARN", area, 'no log = "[GetDateText]: [Root.GetName]: Decision <id>" line (design-guide section 5)')
        if "days_remove" not in b and "days_re_enable" not in b and not n.startswith(P + "_debug"):
            add("WARN", area, "no days_remove / days_re_enable")
        if cost and cct:
            c = cost.group(1)
            # With native cost = N, the engine displays PP separately; the custom label is for treasury cash.
            for area_name, message in aral_pp_cost_label_issues(n, b, loc, langs):
                add("ERROR", area_name, message)
            for tk in re.findall(r"custom_effect_tooltip\s*=\s*(\S+_cost_tt)", cce):
                for lg in langs:
                    if not re.search(r"(?<!\d)" + c + r"(?!\d)", loc[lg].get(tk, "")):
                        add("WARN", area, "political-power cost %s not in tooltip %s (%s)" % (c, tk, lg))
        for var, val, tk in re.findall(r"add_to_variable\s*=\s*\{\s*(\w+)\s*=\s*(-?[\d.]+)\s*tooltip\s*=\s*(\w+)", cre):
            for lg in langs:
                s = loc[lg].get(tk)
                if s is None:
                    add("ERROR", area, "tooltip key %s missing (%s)" % (tk, lg))
                elif fmt(float(val)) not in s.replace(",", "."):
                    add("ERROR", area, "tooltip %s says '%s' but code adds %s to %s" % (tk, s, val, var))
        for g in re.findall(r"\b(" + P + r"_unlocked_\w+)\s*=\s*yes", b):
            if g not in triggers:
                add("ERROR", area, "scripted trigger %s is not defined" % g)

    for area, msg in custom_cost_blocked_key_issues(decisions, loc, langs):
        add("WARN", area, "project-generated custom-cost suffix convention: " + msg)
    if P == "aral":
        for area, msg in aral_treasury_cost_issues(decisions, events):
            add("ERROR", area, msg)
        for area, msg in aral_ownership_issues(decisions, effects, code_all):
            add("ERROR", area, msg)
        for area, msg in aral_initialization_issues(effects):
            add("ERROR", area, msg)
        for area, msg in aral_modifier_issues(dyn, effects):
            add("ERROR", area, msg)
        for area, msg in aral_regional_crisis_issues(events, decisions, effects):
            add("ERROR", area, msg)
        for area, msg in aral_decision_cost_issues(decisions):
            add("ERROR", area, msg)

    # ---------- D. flags ----------
    set_f = collections.Counter(re.findall(r"set_country_flag\s*=\s*(?:\{\s*flag\s*=\s*)?(\w+)", code_all))
    clr_f = set(re.findall(r"clr_country_flag\s*=\s*(\w+)", code_all))
    read_f = collections.Counter(re.findall(r"has_country_flag\s*=\s*(?:\{\s*flag\s*=\s*)?(\w+)", code_all))
    for f in read_f:
        if f not in set_f:
            add("ERROR", "flags", "flag %s is checked but never set (dead gate)" % f)
    for f in set_f:
        if f not in read_f and f not in clr_f:
            add("INFO", "flags", "flag %s is set but never checked" % f)

    # ---------- E. variables ----------
    wr = collections.Counter()
    for m in re.finditer(r"\b(?:set_variable|set_temp_variable|add_to_variable|subtract_from_variable|multiply_variable|divide_variable|round_variable|clamp_variable)\s*=\s*\{\s*(?:var\s*=\s*)?(\w+)", code_all):
        wr[m.group(1)] += 1
    loc_all = "\n".join(v for lg in loc for v in loc[lg].values())
    allocc = collections.Counter(re.findall(r"\b(" + P + r"_[a-z0-9_]+)\b", code_all + "\n" + gui_text + "\n" + loc_all))
    for v, n in wr.items():
        if v.startswith(P) and allocc[v] == n:
            add("WARN", "variables", "%s is written %dx and never read" % (v, n))
    reads = set(re.findall(r"check_variable\s*=\s*\{\s*(?:var\s*=\s*)?(" + P + r"_\w+)", code_all))
    for v in reads:
        if wr[v] == 0 and v not in effects and v not in triggers:
            add("ERROR", "variables", "%s is read but never written" % v)

    # ---------- F. events ----------
    titles, labels = {}, {}
    fired = set(re.findall(r"country_event\s*=\s*\{\s*id\s*=\s*([\w.]+)", code_all)) | set(re.findall(r"country_event\s*=\s*([\w.]+)", code_all))
    for i, b in events.items():
        area = "event " + i
        if i not in fired:
            add("WARN", area, "never fired from any effect in the mechanic")
        if re.search(r"\bhidden\s*=\s*yes", b):
            continue  # a hidden event has no text
        tk = re.search(r"title\s*=\s*(\S+)", b)
        dk = re.search(r"desc\s*=\s*(\S+)", b)
        for lg in langs:
            tt = loc[lg].get(tk.group(1)) if tk else None
            dd = loc[lg].get(dk.group(1)) if dk else None
            if tt is None:
                add("ERROR", area, "title key missing (%s)" % lg)
            if dd is None:
                add("ERROR", area, "desc key missing (%s)" % lg)
            elif not (150 <= len(dd) <= 380) and lg == "en":
                add("WARN", area, "description length %d (target 150-380)" % len(dd))
            if tt and lg == "en":
                if tt in titles:
                    add("WARN", area, "title duplicates event %s" % titles[tt])
                titles[tt] = i
        opts = re.findall(r"\boption\s*=\s*\{", b)
        for m in re.finditer(r"\boption\s*=\s*\{", b):
            ob = b[m.end():match_brace(b, m.end() - 1)]
            nm = re.search(r"name\s*=\s*(\S+)", ob)
            if not nm:
                add("ERROR", area, "option without name")
                continue
            for lg in langs:
                lab = loc[lg].get(nm.group(1))
                if lab is None:
                    add("ERROR", area, "option key %s missing (%s)" % (nm.group(1), lg))
                elif lg == "en":
                    if len(lab) > 35:
                        add("WARN", area, "option label longer than 35: '%s'" % lab)
                    if lab in labels:
                        add("WARN", area, "option label '%s' repeats (%s)" % (lab, labels[lab]))
                    labels[lab] = nm.group(1)
            if len(opts) > 1 and "ai_chance" not in ob:
                add("INFO", area, "option %s has no ai_chance" % nm.group(1))

    # ---------- G. text rules ----------
    for lg in langs:
        for k, v in loc[lg].items():
            low = v.lower()
            for w in BANNED:
                if w in low:
                    add("WARN", "text " + k, "banned phrase '%s' (%s)" % (w, lg))
            if YEAR_RE.search(v):
                add("WARN", "text " + k, "year in text: %s (%s)" % (YEAR_RE.search(v).group(0), lg))
            for c in CAPITALS:
                if c in v:
                    add("INFO", "text " + k, "hardcoded name '%s' (%s); check if a dynamic token fits" % (c, lg))
                    break

    # ---------- H. modifier identifiers vs curated MDC Wiki references / TDF ----------
    wiki = ""
    for wiki_file in glob.glob(os.path.join(a.wiki, "**", "*.md"), recursive=True):
        with open(wiki_file, encoding="utf-8", errors="replace") as handle:
            wiki += handle.read()
    repo_common = ""
    for common_file in glob.glob(os.path.join(root, "common", "**", "*.txt"), recursive=True):
        if not os.path.basename(common_file).lower().startswith(P):
            with open(common_file, encoding="utf-8-sig", errors="replace") as handle:
                repo_common += handle.read()

    for helper in ("ai_hint_pp_cost", "has_political_power"):
        if re.search(r"\b" + helper + r"\b", code_all) and not re.search(r"\b" + helper + r"\b", wiki):
            add("INFO", "cost mechanics", "%s is used but is not documented in the supplied MDC Wiki references; verify it in the target TDF source file" % helper)

    skip = {"icon", "enable", "remove_trigger", "cooldown", "gain_xp", "dynamic", "trigger"}
    for modifier_name, modifier_body in dyn.items():
        modifier_keys = [
            key for key in re.findall(r"^\s*([a-z_0-9]+)\s*=\s*[\w.\-]+\s*$", modifier_body, re.M)
            if key not in skip
        ]
        for key in modifier_keys:
            if not re.search(r"\b" + key + r"\b", wiki) and not re.search(r"\b" + key + r"\b", repo_common):
                add("WARN", "modifier " + modifier_name, "%s was not found in curated MDC Wiki references or other TDF source files; request the target TDF file if it remains undocumented" % key)
        for variable in re.findall(r"=\s*(" + P + r"_\w+)", modifier_body):
            if wr[variable] == 0:
                add("ERROR", "modifier " + modifier_name, "reads variable %s that is never written" % variable)

    # ---------- I. effects / triggers used vs defined ----------
    called = collections.Counter(re.findall(r"\b([a-z][a-z0-9_]*)\s*=\s*yes\b", code_all))
    ext = []
    KEYWORDS = {"always", "fire_only_once", "is_triggered_only", "visible_when_empty", "instant_build", "hidden",
                "force_update_dynamic_modifier", "newline", "show_effect_tooltip", "is_good", "major", "hidden_ideas", "has_war"}
    for n, c in called.items():
        if n in effects or n in triggers or n in KEYWORDS:
            continue
        defined = re.search(r"^" + re.escape(n) + r"\s*=\s*\{", repo_common, re.M)
        if n.startswith(P):
            add("ERROR", "effects", "%s is called %dx but defined nowhere in the mechanic" % (n, c))
        elif not defined:
            ext.append(n)
    for n in effects:
        if called[n] == 0 and n not in code_all.replace("%s = {" % n, "", 1):
            add("WARN", "effects", "%s is defined but never called" % n)
    if ext:
        add("INFO", "effects", "identifiers with '= yes' not defined in the available TDF files; check MDC Wiki and request the target TDF definition if undocumented: " + ", ".join(sorted(ext)))
    for ext_name in ("modify_treasury_effect",):
        if ext_name in code_all and not re.search(r"\b" + ext_name + r"\b", wiki + repo_common):
            add("INFO", "effects", "%s is not documented with an implementation in the available TDF references; request the target TDF effect definition before relying on its side effects" % ext_name)

    # ---------- J. scripted GUI vs .gui / .gfx ----------
    gui_names = set(re.findall(r'\bname\s*=\s*"?([\w.\-]+)"?', gui_text))
    sg_names = set()
    for sec in ("effects", "triggers", "properties"):
        for m in re.finditer(r"\b" + sec + r"\s*=\s*\{", sg_text):
            e = match_brace(sg_text, m.end() - 1)
            sg_names |= set(blocks(sg_text[m.end():e], 0).keys())
    # the engine appends suffixes to the element name: <el>_visible, <el>_click, ...
    suffix = re.compile(r"_(?:visible|click_enabled|click|right_click|ontoggle|tooltip|enabled|shift_click|ctrl_click)$")
    sg_names = {suffix.sub("", x) for x in sg_names}
    for nme in sorted(sg_names):
        if nme not in gui_names:
            add("ERROR", "scripted_gui", "element %s is not in any .gui file" % nme)
    sprites = set(re.findall(r'spriteType\s*=\s*"?(GFX_[\w]+)"?', gui_text))
    defined_sp = set(re.findall(r'name\s*=\s*"(GFX_[\w]+)"', gfx_text))
    for sname in sorted(sprites):
        if sname.startswith("GFX_" + P) and sname not in defined_sp:
            add("ERROR", "gui", "sprite %s used in .gui but not defined in .gfx" % sname)
    for tex in set(re.findall(r'texturefile\s*=\s*"([^"]+)"', gfx_text)):
        if not os.path.exists(os.path.join(root, tex)):
            add("ERROR", "gfx", "texture file missing: %s" % tex)

    for c in blocks(cat_text, 0):
        if not re.match(r"[A-Z]{2,3}_", c):
            add("INFO", "category " + c, "id is not <TAG>_<theme>_category (design-guide section 5)")

    # ---------- K. unused loc keys ----------
    referenced = set()
    for n in decisions:
        referenced |= {n, n + "_desc"}
    for n in dyn:
        referenced |= {n, n + "_desc"}
    for c in blocks(cat_text, 0):
        referenced |= {c, c + "_desc"}
    for i in events:
        referenced |= {i + ".t", i + ".d"}
    referenced |= implied_custom_cost_localisation_keys(decisions)
    big = code_all + "\n" + gui_text + "\n" + "\n".join(loc.get("en", {}).values())
    for k in loc.get("en", {}):
        if k in referenced:
            continue
        if not re.search(r"(?<![\w.])" + re.escape(k) + r"(?![\w])", big) and not k.startswith(tuple(i + "." for i in events)):
            add("INFO", "loc", "key %s is defined but never referenced" % k)

    # ---------- report ----------
    order = ["ERROR", "WARN", "INFO"]
    for sev in order:
        items = OUT.get(sev, [])
        print("== %s (%d)" % (sev, len(items)))
        for area, msg in items:
            print("  [%s] %s" % (area, msg))
    print("\nSUMMARY files=%d decisions=%d events=%d effects=%d langs=%s loc_keys=%d | ERROR=%d WARN=%d INFO=%d" % (
        len(files), len(decisions), len(events), len(effects), ",".join(langs), len(L),
        len(OUT["ERROR"]), len(OUT["WARN"]), len(OUT["INFO"])))
    if a.json:
        output_path = os.path.abspath(a.json)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({k: v for k, v in OUT.items()}, handle, ensure_ascii=False, indent=1)
            handle.write("\n")
    return 1 if OUT["ERROR"] else 0


RULES = """ERROR  yml without BOM / bare LF / brace mismatch / duplicate loc key / EN-RU key parity
ERROR  decision: loc key missing, generic treasury price key differs from the full debit, non-always treasury gate, duplicate debt transaction,
       tooltip number differs from the code, undefined scripted trigger
ERROR  Aral events and decisions must not gate treasury spending on current balance; negative treasury is financed by TDF debt
ERROR  flag checked but never set; variable read but never written; effect called but undefined
ERROR  event: missing title/desc/option keys; scripted GUI element missing in .gui; sprite/texture missing
ERROR  Aral: decisions, monthly tick and recalculation are gated by KAZ ownership of state 717; state modifier is persistent
WARN   spaces, no ai_will_do, no decision log line, variable written but never read,
       event length/label rules, banned phrases, years in text, modifier IDs absent from supplied MDC/TDF references, unused effects
INFO   hardcoded capitals, flags set but unused, undocumented cost helpers, unresolved TDF identifiers, unreferenced loc keys"""

if __name__ == "__main__":
    sys.exit(main())
