#!/usr/bin/env python3
"""Month-by-month simulation of the Aral Sea mechanic, built from the REAL code.

Every number (drift, fill rate, level formula, modifier coefficients, project length, price,
debt, water points, requirements, level gates, exclusions) is parsed from
  common/scripted_effects/aral_sea_effects.txt
  common/decisions/aral_sea_decisions.txt
  common/dynamic_modifiers/aral_sea_modifiers.txt
  common/history/countries/KAZ - Kazakhstan.txt   (start treasury)
so the report cannot drift away from the code. Money and political power income are NOT in
the repo (they come from the base mod), so they are parameters: run a sweep to see how much the
answer depends on them.

    python3 -I skills/md-hoi4-country-content/scripts/aral_model_sim.py mdredux
    python3 -I skills/md-hoi4-country-content/scripts/aral_model_sim.py mdredux --income 0.2 --route dam2 --sibaral win --verbose
"""
import argparse, datetime, json, math, os, re, sys

MONTH = 30.4375
PRIORITY = ["aral_loan", "aral_ifas", "aral_channel", "aral_kokaral", "aral_uzb", "aral_aklak",
            "aral_irrigation", "aral_fish", "aral_saxaul1", "aral_ormany", "aral_amanotkel",
            "aral_phase2", "aral_dam2", "aral_saxaul2", "aral_transboundary", "aral_sibaral"]


def rd(p):
    return open(p, encoding="utf-8-sig").read().replace("\r", "")


def nocomment(t):
    return re.sub(r"#[^\n]*", "", t)


def brace(t, i):
    d = 0
    for k in range(i, len(t)):
        if t[k] == "{":
            d += 1
        elif t[k] == "}":
            d -= 1
            if d == 0:
                return k
    return -1


def sect(t, name):
    m = re.search(r"\b" + re.escape(name) + r"\s*=\s*\{", t)
    if not m:
        return ""
    return t[m.end():brace(t, m.end() - 1)]


def f(s):
    return float(s)


def parse(root):
    eff = nocomment(rd(os.path.join(root, "common/scripted_effects/aral_sea_effects.txt")))
    dec = nocomment(rd(os.path.join(root, "common/decisions/aral_sea_decisions.txt")))
    dyn = nocomment(rd(os.path.join(root, "common/dynamic_modifiers/aral_sea_modifiers.txt")))
    hist = rd(os.path.join(root, "common/history/countries/KAZ - Kazakhstan.txt"))
    C = {}
    upd, drift = sect(eff, "update_aral_sea"), sect(eff, "aral_calc_drift")
    m = re.search(r"var = aral_sea_restoration min = (-?[\d.]+) max = (-?[\d.]+)", upd)
    C["r_min"], C["r_max"] = f(m.group(1)), f(m.group(2))
    C["deficit_base"] = f(re.search(r"aral_deficit = ([\d.]+) \}", upd).group(1))
    C["level_k"] = f(re.search(r"multiply_variable = \{ aral_sea_level = ([\d.]+)", upd).group(1))
    C["level_0"] = f(re.search(r"add_to_variable = \{ aral_sea_level = ([\d.]+)", upd).group(1))
    C["mods"] = {k: f(v) for k, v in re.findall(r"multiply_variable = \{ (aral_mod_\w+) = (-?[\d.]+) \}", upd)}
    C["bonus"] = re.findall(r"has_country_flag = (\w+) \} add_to_variable = \{ (aral_mod_\w+) = (-?[\d.]+)", upd)
    drifts = re.findall(r"aral_drift = (-?[\d.]+)", drift)
    C["drift0"], C["drift_dam"] = f(drifts[0]), f(drifts[1])
    C["drift_adj"] = {fl: f(v) for fl, v in re.findall(r"has_country_flag = (\w+) \} add_to_variable = \{ aral_drift = (-?[\d.]+)", drift)}
    C["drift_floor"] = f(re.search(r"aral_sea_restoration < (-?[\d.]+) \} \} set_variable = \{ aral_drift = 0", drift).group(1))
    C["fill_rate"] = f(re.search(r"multiply_variable = \{ aral_fill = ([\d.]+)", drift).group(1))
    C["fill_min"] = f(re.search(r"aral_fill < ([\d.]+) \} \} set_variable = \{ aral_fill = ([\d.]+)", drift).group(2))
    C["dyn_map"] = re.findall(r"^\s*([a-z_]+)\s*=\s*(aral_mod_\w+)", dyn, re.M)
    t = re.search(r"var = treasury value = ([\d.]+)", hist)
    C["treasury0"] = f(t.group(1)) if t else 0.0
    C["debt0"] = f(re.search(r"var = debt value = ([\d.]+)", hist).group(1))
    D = {}
    cat = re.search(r"\n(\w+)\s*=\s*\{", "\n" + dec)
    body = sect(dec, cat.group(1))
    for m in re.finditer(r"\n\t(aral_\w+)\s*=\s*\{", "\n" + body):
        pass
    pos = 0
    for m in re.finditer(r"(?m)^\t(aral_\w+)\s*=\s*\{", body):
        n = m.group(1)
        e = brace(body, m.end() - 1)
        b = body[m.end():e]
        if n.startswith("aral_debug"):
            continue
        av = sect(b, "available")
        ce, re_ = sect(b, "complete_effect"), sect(b, "remove_effect")
        d = {"days": int(f(re.search(r"days_remove = (\d+)", b).group(1))),
             "pp": int(re.search(r"^\s*cost = (\d+)", b, re.M).group(1)) if re.search(r"^\s*cost = (\d+)", b, re.M) else 0,
             "tre": abs(f(re.search(r"treasury_change = (-?[\d.]+)", ce).group(1))),
             "debt": f(re.search(r"debt_change = (-?[\d.]+)", ce).group(1)) if "debt_change" in ce else 0.0}
        thr = re.search(r"custom_cost_trigger = \{ check_variable = \{ treasury > ([\d.]+)", b)
        d["gate"] = f(thr.group(1)) if thr else d["tre"]
        d["pending"] = sum(f(x) for x in re.findall(r"add_to_variable = \{ aral_pending = ([\d.]+)", re_)) if "random_list" not in re_ else 0.0
        d["relief"] = sum(f(x) for x in re.findall(r"add_to_variable = \{ aral_relief = ([\d.]+)", re_))
        orb = ""
        for om in re.finditer(r"\bOR\s*=\s*\{", av):
            orb += av[om.end():brace(av, om.end() - 1)]
        av_wo = av.replace(orb, "") if orb else av
        d["needs"] = [x for x in re.findall(r"has_country_flag = aral_(\w+)_done", av_wo)]
        d["any"] = re.findall(r"has_country_flag = aral_(\w+)_done", orb)
        d["excl"] = re.findall(r"NOT = \{ has_country_flag = aral_(\w+)_started", av)
        g = re.search(r"aral_sea_level > ([\d.]+)", av)
        d["level_gate"] = f(g.group(1)) if g else 0.0
        if "random_list" in re_:
            w = re.search(r"(\d+) = \{\s*add_to_variable = \{ aral_pending = ([\d.]+)", re_)
            d["sib_p"] = int(w.group(1)) / 100.0
            d["sib_pending"] = f(w.group(2))
        D[n[5:]] = d  # strip "aral_"
    return C, D


def sim(C, D, income, pp_month, route, sib, months, t0=None, pp0=0.0, verbose=False):
    r, pend, relief = 0.0, 0.0, 0.0
    tre = C["treasury0"] if t0 is None else t0
    pp = pp0
    done, started, running = set(), set(), []
    spent_t, spent_d, spent_pp = 0.0, 0.0, 0
    hist, log = [], []
    order = [n for n in PRIORITY if n[5:] in D]
    skip = {"dam2"} if route == "phase2" else {"phase2"}
    for mth in range(months):
        day = mth * MONTH
        tre += income
        pp += pp_month
        for fin, n in sorted([x for x in running if x[0] <= day]):
            running.remove((fin, n))
            d = D[n]
            done.add(n)
            if "sib_p" in d:
                if sib == "win":
                    pend += d["sib_pending"]
            else:
                pend += d["pending"]
            relief += d["relief"]
            if n == "fish":
                relief += 1  # event aral_sea.2 option a
            log.append((mth, "done", n))
        for n in order:
            k = n[5:]
            if k in skip or k in started:
                continue
            d = D[k]
            if any(x not in done for x in d["needs"]):
                continue
            if d["any"] and not any(x in done for x in d["any"]):
                continue
            if any(x in started for x in d["excl"]):
                continue
            lvl = C["level_0"] + C["level_k"] * r
            if lvl <= d["level_gate"] + (0 if d["level_gate"] == 0 else -0.0) and d["level_gate"] > 0:
                continue
            if tre <= d["gate"] or pp < d["pp"]:
                continue
            tre -= d["tre"]
            pp -= d["pp"]
            spent_t += d["tre"]
            spent_d += d["debt"]
            spent_pp += d["pp"]
            started.add(k)
            running.append((day + d["days"], k))
            log.append((mth, "start", k))
        # monthly tick
        drift = C["drift0"]
        if "kokaral" in done:
            drift = C["drift_dam"]
            for fl, v in C["drift_adj"].items():
                if fl.replace("aral_", "").replace("_done", "") in done:
                    drift += v
        if drift < 0.001:
            drift = 0.0
        if r < C["drift_floor"]:
            drift = 0.0
        fill = pend * C["fill_rate"]
        if pend > 0.001 and fill < C["fill_min"]:
            fill = C["fill_min"]
        fill = min(fill, pend)
        if pend < 0.001 or r > 99.9:
            fill = 0.0
        r = max(C["r_min"], min(C["r_max"], r - drift + fill))
        pend = max(0.0, pend - fill)
        if r > 99.9:
            pend = 0.0
        hist.append({"m": mth, "r": r, "level": C["level_0"] + C["level_k"] * r, "pend": pend, "relief": relief,
                     "deficit": max(0.0, min(200.0, C["deficit_base"] - r - relief)), "drift": drift, "fill": fill})
    return {"hist": hist, "log": log, "spent_t": spent_t, "spent_d": spent_d, "spent_pp": spent_pp, "done": done}


def date(start, m):
    d = start + datetime.timedelta(days=int(m * MONTH))
    return "%04d-%02d" % (d.year, d.month)


def milestones(res, start, levels=(36, 38, 40, 42, 44, 46)):
    h = res["hist"]
    out = {}
    for L in levels:
        for x in h:
            if x["level"] >= L - 1e-9:
                out[L] = x["m"]
                break
    last = max([m for m, k, n in res["log"] if k == "done"] or [0])
    plateau = None  # first month AFTER the last finished project when the pool is drained and drying is over
    for x in h:
        if x["m"] >= last and x["pend"] < 0.05 and x["drift"] == 0.0:
            plateau = x["m"]
            break
    peak = max(h, key=lambda x: x["level"])
    return out, plateau, last, peak


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="mdredux")
    ap.add_argument("--income", type=float, help="treasury income per month, bn (not in the repo)")
    ap.add_argument("--pp", type=float, default=45.0, help="political power per month (default 1.5/day)")
    ap.add_argument("--route", choices=["phase2", "dam2"], default="phase2")
    ap.add_argument("--sibaral", choices=["win", "lose"], default="lose")
    ap.add_argument("--start", default="2000-01-01")
    ap.add_argument("--months", type=int, default=600)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    C, D = parse(a.root)
    start = datetime.date.fromisoformat(a.start)
    print("# Constants parsed from the code")
    print("level = %.0f + %.2f x restoration (restoration %.0f..%.0f)  =>  %.1f m .. %.1f m" % (
        C["level_0"], C["level_k"], C["r_min"], C["r_max"], C["level_0"] + C["level_k"] * C["r_min"], C["level_0"] + C["level_k"] * C["r_max"]))
    print("drift: %.2f%%/month, with Kokaral %.2f%% %s, floor at %.1f" % (C["drift0"], C["drift_dam"], C["drift_adj"], C["drift_floor"]))
    print("fill: %.0f%% of pending per month, minimum %.1f" % (C["fill_rate"] * 100, C["fill_min"]))
    print("deficit = %.0f - restoration - relief; start treasury %.3f bn, start debt %.1f" % (C["deficit_base"], C["treasury0"], C["debt0"]))
    print("modifier coefficients per 1 deficit:", C["mods"])
    print()
    print("# Projects (parsed)")
    print("%-14s %5s %4s %6s %6s %6s %6s  needs / gate / excl" % ("decision", "days", "PP", "tre", "debt", "water", "relief"))
    for n, d in D.items():
        extra = ",".join(d["needs"]) + (" any(%s)" % ",".join(d["any"]) if d["any"] else "") + (" lvl>%g" % d["level_gate"] if d["level_gate"] else "") + (" excl(%s)" % ",".join(d["excl"]) if d["excl"] else "")
        w = d["pending"] if "sib_p" not in d else "%g@%d%%" % (d["sib_pending"], d["sib_p"] * 100)
        print("%-14s %5d %4d %6.2f %6.2f %6s %6g  %s" % (n, d["days"], d["pp"], d["tre"], d["debt"], w, d["relief"], extra))
    for route in ("phase2", "dam2"):
        water = sum(d["pending"] for k, d in D.items() if k != ("dam2" if route == "phase2" else "phase2"))
        rel = sum(d["relief"] for d in D.values()) + 1
        tre = sum(d["tre"] for k, d in D.items() if k != ("dam2" if route == "phase2" else "phase2"))
        dbt = sum(d["debt"] for k, d in D.items() if k != ("dam2" if route == "phase2" else "phase2"))
        sibp = D["sibaral"]["sib_pending"]
        print("\nroute %-6s: water %.0f (+%.0f if Sibaral wins), relief %.0f; money %.2f from treasury + %.2f borrowed = %.2f bn" % (route, water, sibp, rel, tre, dbt, tre + dbt))
        print("   ceiling without drying losses: restoration %.0f -> %.1f m;  with Sibaral %.0f -> %.1f m (cap %.0f = %.1f m)" % (
            water, C["level_0"] + C["level_k"] * water, min(water + sibp, 100), C["level_0"] + C["level_k"] * min(water + sibp, 100), 100, C["level_0"] + C["level_k"] * 100))

    # nothing is done
    h = sim(C, D, 0.0, 0.0, "phase2", "lose", a.months)["hist"]
    floor_m = next((x["m"] for x in h if x["r"] <= C["r_min"] + 0.2), None)
    print("\n# If the player does nothing: -30 (%.1f m) reached in month %s (%s)" % (
        C["level_0"] + C["level_k"] * C["r_min"], floor_m, date(start, floor_m) if floor_m else "-"))

    print("\n# Sweep: how fast and how high, by treasury income (bn per month), start %s" % a.start)
    print("%-7s %-6s %-5s | %-8s %-8s %-8s %-8s | %-8s %-8s | %s" % ("income", "route", "sib", "36 m", "40 m", "42 m", "44 m", "last", "plateau", "final level / deficit / spent(bn) / PP"))
    rows = []
    incomes = [a.income] if a.income is not None else [0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 50.0]
    for inc in incomes:
        for route in ([a.route] if a.income is not None else ["phase2", "dam2"]):
            for sib in ([a.sibaral] if a.income is not None else ["lose", "win"]):
                res = sim(C, D, inc, a.pp, route, sib, a.months)
                ms, plateau, last, peak = milestones(res, start)
                fin = res["hist"][-1]
                g = lambda L: date(start, ms[L]) if L in ms else "never"
                print("%-7s %-6s %-5s | %-8s %-8s %-8s %-8s | %-8s %-8s | %.1f m / %.0f / %.2f / %d" % (
                    inc if inc < 10 else "inf", route, sib, g(36), g(40), g(42), g(44), date(start, last), date(start, plateau) if plateau else "-",
                    fin["level"], fin["deficit"], res["spent_t"] + res["spent_d"], res["spent_pp"]))
                rows.append({"income": inc, "route": route, "sib": sib, "milestones": ms, "last": last, "plateau": plateau, "final": fin})
                if a.verbose and a.income is not None:
                    for m, k, n in res["log"]:
                        print("   %s  month %3d  %-5s %s" % (date(start, m), m, k, n))
                    for m in (0, 12, 24, 36, 60, 84, 120, 180, 240):
                        x = res["hist"][min(m, len(res["hist"]) - 1)]
                        print("   month %3d (%s): level %.2f m, restoration %.1f, pending %.1f, relief %.0f, deficit %.0f" % (m, date(start, m), x["level"], x["r"], x["pend"], x["relief"], x["deficit"]))
    # effect size at key states
    print("\n# Penalty at selected deficits (country level, as shown by the dynamic modifier)")
    names = dict((v, k) for k, v in C["dyn_map"])
    for deficit in (130, 100, 60, 30, 8, 0):
        print("deficit %3d: " % deficit + ", ".join("%s %+.1f%%" % (names.get(k, k).replace("_modifier", ""), c * deficit * 100) for k, c in C["mods"].items()))
    if a.json:
        json.dump({"constants": C, "projects": D, "rows": rows}, open(a.json, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
