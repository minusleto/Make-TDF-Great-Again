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
    for m in re.finditer(r"\bcountry_event\s*=\s*\{", ev_text):
        e = match_brace(ev_text, m.end() - 1)
        b = ev_text[m.end():e]
        i = re.search(r"\bid\s*=\s*(\S+)", b)
        if i:
            events[i.group(1)] = b

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
        for k in re.findall(r"^\s*([a-z_0-9]+)\s*=\s*[\w.\-]+\s*$", b, re.M):
            if k in skip:
                continue
            if not re.search(r"\b" + k + r"\b", wiki) and not re.search(r"\b" + k + r"\b", repo_common):
                add("WARN", "modifier " + n, "%s found neither in wiki nor in other repo files: verify in game" % k)
        for v in re.findall(r"=\s*(" + P + r"_\w+)", b):
            if wr[v] == 0:
                add("ERROR", "modifier " + n, "reads variable %s that is never written" % v)

    # ---------- I. effects / triggers used vs defined ----------
    called = collections.Counter(re.findall(r"\b([a-z][a-z0-9_]*)\s*=\s*yes\b", code_all))
    ext = []
    KEYWORDS = {"always", "fire_only_once", "is_triggered_only", "visible_when_empty", "instant_build", "hidden",
                "force_update_dynamic_modifier", "newline", "show_effect_tooltip", "is_good", "major", "hidden_ideas"}
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
ERROR  decision: loc key missing, cost charged but not shown in label, treasury gate below price,
       tooltip number differs from the code, undefined scripted trigger
ERROR  flag checked but never set; variable read but never written; effect called but undefined
ERROR  event: missing title/desc/option keys; scripted GUI element missing in .gui; sprite/texture missing
WARN   spaces, no ai_will_do, price not in label/tooltip, variable written but never read,
       event length/label rules, banned phrases, years in text, unknown modifier names, unused effects
INFO   hardcoded capitals, flags set but unused, external identifiers, unreferenced loc keys"""

if __name__ == "__main__":
    sys.exit(main())
