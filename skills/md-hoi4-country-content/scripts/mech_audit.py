#!/usr/bin/env python3
"""Mechanic audit for MD/HOI4 content that is NOT a focus tree: decisions, events,
scripted effects/triggers, dynamic modifiers, scripted GUI, .gui/.gfx and localisation.

Usage (from the repository root):
    python3 -I skills/md-hoi4-country-content/scripts/mech_audit.py mdredux --prefix aral
    python3 -I skills/md-hoi4-country-content/scripts/mech_audit.py mdredux --prefix aral --json out.json

The prefix selects the files (by file name) and the identifiers (flags, variables, loc keys)
that belong to the mechanic. Exit code 1 when there is at least one ERROR.
The checks come from skills/md-hoi4-country-content (loc-style.md, pitfalls.md) and from bugs
that were found by hand in real reviews; each rule is listed in RULES at the bottom.
"""
import argparse, collections, glob, json, os, re, sys

BANNED = ["strengthen ties", "mutual benefit", "significant", "foothold", "valuable",
          "comprehensive", "ensuring", "paving the way", "foster"]
CAPITALS = ["Moscow", "Beijing", "Astana", "Nur-Sultan", "Tashkent", "Ankara", "Tehran",
            "Washington", "Bishkek", "Dushanbe", "Москва", "Москв", "Пекин", "Ташкент",
            "Астан", "Анкар", "Тегеран", "Бишкек", "Душанбе"]
YEAR_RE = re.compile(r"\b(?:200\d|201\d|202[0-5])\b")
OUT = collections.defaultdict(list)


def add(sev, area, msg):
    OUT[sev].append((area, msg))


def rd(path):
    b = open(path, "rb").read()
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
        blocked = match.group(1) + "_blocked"
        for lang in langs:
            if blocked not in loc.get(lang, {}):
                issues.append(("decision " + decision, "blocked custom-cost key %s is missing (%s)" % (blocked, lang)))
    return issues


def implied_custom_cost_localisation_keys(decisions):
    """Return localisation keys used implicitly by custom_cost_text suffix conventions."""
    implied = set()
    for body in decisions.values():
        match = re.search(r"custom_cost_text\\s*=\\s*(\\S+)", body)
        if match:
            base = match.group(1)
            implied.add(base + "_blocked")
            implied.add(base + "_tooltip")
    return implied


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
        if not re.search(r"\bowns_state\s*=\s*717\b", available):
            issues.append(("decision " + decision, "available must require owns_state = 717"))
        if re.search(r"\bcontrols_state\s*=\s*717\b", available):
            issues.append(("decision " + decision, "use owns_state = 717, not controls_state = 717"))

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

    state_update = effects.get("aral_state_update", "")
    if not re.search(r"is_owned_by\s*=\s*ROOT", state_update):
        issues.append(("scripted_effect aral_state_update", "state modifier values must recalculate only while the state is owned by ROOT"))
    if re.search(r"remove_dynamic_modifier\s*=\s*\{\s*modifier\s*=\s*aral_state_modifier\b", code_all):
        issues.append(("state modifier", "aral_state_modifier must remain on the state when ownership changes; do not remove it"))
    return issues


def num(s):
    try:
        return float(s)
    except Exception:
        return None


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="mdredux")
    ap.add_argument("--prefix", default="aral")
    ap.add_argument("--wiki", default="wiki/docs")
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
        tre = re.search(r"treasury_change\s*=\s*(-?[\d.]+)", cce)
        dbt = re.search(r"debt_change\s*=\s*(-?[\d.]+)", cce)
        thr = re.search(r"custom_cost_trigger\s*=\s*\{\s*check_variable\s*=\s*\{\s*treasury\s*>\s*([\d.]+)", b)
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
            for lg in langs:
                lab = loc[lg].get(cct.group(1), "")
                if not re.search(r"(?<!\d)" + c + r"(?!\d)", lab):
                    add("ERROR", area, "political-power cost %s is charged but not shown in label %s (%s): '%s'" % (c, cct.group(1), lg, lab))
            for tk in re.findall(r"custom_effect_tooltip\s*=\s*(\S+_cost_tt)", cce):
                for lg in langs:
                    if not re.search(r"(?<!\d)" + c + r"(?!\d)", loc[lg].get(tk, "")):
                        add("WARN", area, "political-power cost %s not in tooltip %s (%s)" % (c, tk, lg))
        if tre and thr:
            v, th = abs(float(tre.group(1))), float(thr.group(1))
            if th < v - 0.0101:
                add("ERROR", area, "treasury gate %s is lower than the price %s: the decision can be started without the money" % (th, v))
            elif th > v + 1e-9:
                add("WARN", area, "treasury gate %s is higher than the price %s" % (th, v))
        if tre and cct:
            v = abs(float(tre.group(1)))
            for lg in langs:
                lab = loc[lg].get(cct.group(1), "")
                if fmt(v) not in lab.replace(",", "."):
                    add("WARN", area, "price %s not found in cost label (%s): '%s'" % (fmt(v), lg, lab))
        if tre and dbt:
            v, d = abs(float(tre.group(1))), float(dbt.group(1))
            for tk in re.findall(r"custom_effect_tooltip\s*=\s*(\S+_cost_tt)", cce):
                for lg in langs:
                    s = loc[lg].get(tk, "").replace(",", ".")
                    miss = [x for x in (fmt(v), fmt(d), fmt(v + d)) if x not in s]
                    if miss:
                        add("WARN", area, "tooltip %s (%s) lacks %s (treasury %s + debt %s)" % (tk, lg, ",".join(miss), fmt(v), fmt(d)))
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
        add("ERROR", area, msg)
    if P == "aral":
        for area, msg in aral_ownership_issues(decisions, effects, code_all):
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

    # ---------- H. dynamic modifiers vs wiki / repo ----------
    wiki = ""
    for f in glob.glob(os.path.join(a.wiki, "**", "*.md"), recursive=True):
        wiki += open(f, encoding="utf-8", errors="replace").read()
    repo_common = ""
    for f in glob.glob(os.path.join(root, "common", "**", "*.txt"), recursive=True):
        if not os.path.basename(f).lower().startswith(P):
            repo_common += open(f, encoding="utf-8-sig", errors="replace").read()
    skip = {"icon", "enable", "remove_trigger", "cooldown", "gain_xp", "dynamic", "trigger"}
    for n, b in dyn.items():
        ks = [k for k in re.findall(r"^\s*([a-z_0-9]+)\s*=\s*[\w.\-]+\s*$", b, re.M) if k not in skip]
        if len(ks) > 6:
            add("WARN", "modifier " + n, "%d modifiers (balance.md: 3-5 per spirit, capstone up to 6)" % len(ks))
        for k in ks:
            if not re.search(r"\b" + k + r"\b", wiki) and not re.search(r"\b" + k + r"\b", repo_common):
                add("WARN", "modifier " + n, "%s found neither in wiki nor in other repo files: verify in game" % k)
        for v in re.findall(r"=\s*(" + P + r"_\w+)", b):
            if wr[v] == 0:
                add("ERROR", "modifier " + n, "reads variable %s that is never written" % v)

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
        add("INFO", "effects", "external identifiers with '= yes' (verify they exist in the base mod): " + ", ".join(sorted(ext)))
    for ext_name in ("modify_treasury_effect", "modify_debt_effect"):
        if ext_name in code_all and not re.search(ext_name, repo_common):
            add("INFO", "effects", "%s is not used anywhere else in the repo" % ext_name)

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
        json.dump({k: v for k, v in OUT.items()}, open(a.json, "w"), ensure_ascii=False, indent=1)
    return 1 if OUT["ERROR"] else 0


RULES = """ERROR  yml without BOM / bare LF / brace mismatch / duplicate loc key / EN-RU key parity
ERROR  decision: loc key missing, blocked custom-cost localisation missing, cost charged but not shown in label, treasury gate below price,
       tooltip number differs from the code, undefined scripted trigger
ERROR  flag checked but never set; variable read but never written; effect called but undefined
ERROR  event: missing title/desc/option keys; scripted GUI element missing in .gui; sprite/texture missing
ERROR  Aral: decisions, monthly tick and recalculation are gated by KAZ ownership of state 717; state modifier is persistent
WARN   spaces, no ai_will_do, no decision log line, spirit with more than 6 modifiers, price not in label/tooltip, variable written but never read,
       event length/label rules, banned phrases, years in text, unknown modifier names, unused effects
INFO   hardcoded capitals, flags set but unused, external identifiers, unreferenced loc keys"""

if __name__ == "__main__":
    sys.exit(main())
