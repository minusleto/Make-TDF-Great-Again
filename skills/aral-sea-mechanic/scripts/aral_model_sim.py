#!/usr/bin/env python3
"""Month-by-month Monte Carlo simulation of the Aral Sea mechanic, built from the REAL code.

Everything is parsed from the mod files, nothing is typed in:
  common/scripted_effects/aral_sea_effects.txt   level formula, drift, fill, yearly hydrology, dike risk
  common/decisions/aral_sea_decisions.txt        length, price, debt, water, relief, requirements, gates
  events/aral_sea_events.txt                     dry-year loss, dike rebuild, price of the choices
  --treasury                  starting treasury (default: KAZ 2000 baseline, 0.245 bn)
Treasury income and political power per month are not defined by this mechanic's source files, so
they remain explicit simulation parameters. The player follows a fixed greedy policy (cheapest unlocked project first).

    python3 -I skills/aral-sea-mechanic/scripts/aral_model_sim.py mdredux
    python3 -I skills/aral-sea-mechanic/scripts/aral_model_sim.py mdredux --income 0.1 --route phase2 --dike yes --once --seed 3
"""
import argparse, datetime, os, random, re, statistics, sys

MONTH = 30.4375
PRIORITY = ["dike", "ifas", "loan", "channel", "kokaral", "uzb", "aklak", "irrigation", "fish", "saxaul1",
            "saxaul2", "amanotkel", "phase2", "dam2"]


def rd(p):
    with open(p, encoding="utf-8-sig") as handle:
        return handle.read().replace("\r", "")


def nc(t):
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
    return t[m.end():brace(t, m.end() - 1)] if m else ""


def fl(x):
    return float(x)


def parse(root, treasury0=0.245):
    eff = nc(rd(os.path.join(root, "common/scripted_effects/aral_sea_effects.txt")))
    dec = nc(rd(os.path.join(root, "common/decisions/aral_sea_decisions.txt")))
    evt = nc(rd(os.path.join(root, "events/aral_sea_events.txt")))
    upd, drift, tick = sect(eff, "update_aral_sea"), sect(eff, "aral_calc_drift"), sect(eff, "aral_monthly_tick")
    C = {}
    m = re.search(r"var = aral_sea_restoration min = (-?[\d.]+) max = (\S+)", upd)
    C["r_min"] = fl(m.group(1))
    C["cap0"] = fl(re.search(r"set_variable = \{ aral_cap = ([\d.]+) \}", upd).group(1))
    C["caps"] = [(f.replace("_done", ""), fl(v)) for f, v in re.findall(r"has_country_flag = aral_(\w+) \} set_variable = \{ aral_cap = ([\d.]+)", upd)]
    C["r_max"] = max(v for f, v in C["caps"])
    C["dry_base"] = fl(re.search(r"set_variable = \{ aral_dry_loss = ([\d.]+) \}", upd).group(1))
    C["dry_adj"] = [(f, (-1 if o == "subtract_from" else 1) * fl(v)) for f, o, v in re.findall(r"has_country_flag = aral_(\w+)_done \} (subtract_from|add_to)_variable = \{ aral_dry_loss = ([\d.]+)", upd)]
    C["deficit_base"] = fl(re.search(r"aral_deficit = ([\d.]+) \}", upd).group(1))
    C["level_k"] = fl(re.search(r"multiply_variable = \{ aral_sea_level = ([\d.]+)", upd).group(1))
    C["level_0"] = fl(re.search(r"add_to_variable = \{ aral_sea_level = ([\d.]+)", upd).group(1))
    C["mods"] = {k: fl(v) for k, v in re.findall(r"multiply_variable = \{ (aral_mod_\w+) = (-?[\d.]+) \}", upd)}
    C["drift0"] = fl(re.search(r"set_variable = \{ aral_drift = (-?[\d.]+) \}", drift).group(1))
    C["drift_adj"] = {f: fl(v) for f, v in re.findall(r"has_country_flag = aral_(\w+)_done \} add_to_variable = \{ aral_drift = (-?[\d.]+)", drift)}
    C["fill_rate"] = fl(re.search(r"multiply_variable = \{ aral_fill = ([\d.]+)", drift).group(1))
    C["fill_min"] = fl(re.search(r"aral_fill < ([\d.]+) \} \} set_variable = \{ aral_fill = ([\d.]+)", drift).group(2))
    C["p_dry"] = int(re.search(r"(\d+) = \{ country_event = \{ id = aral_sea\.1", tick).group(1)) / 100
    m = re.search(r"(\d+) = \{ add_to_variable = \{ aral_pending = ([\d.]+)", tick)
    C["p_wet"], C["wet_pts"] = int(m.group(1)) / 100, fl(m.group(2))
    C["p_dike"] = int(re.search(r"(\d+) = \{ country_event = \{ id = aral_sea\.2", tick).group(1)) / 100
    pos = {int(m.group(1)): m.start() for m in re.finditer(r"(?m)^country_event = \{\n\tid = aral_sea\.(\d+)", evt)}  # definitions only (line start), not calls
    def ev(n):
        later = [v for k, v in pos.items() if v > pos[n]]
        return evt[pos[n]:min(later)] if later else evt[pos[n]:]
    e1 = ev(1)
    C["dry_buy"] = abs(fl(re.search(r"treasury_change = (-?[\d.]+)", e1).group(1)))
    C["dry_pp"] = fl(re.search(r"add_political_power = -(\d+)", e1).group(1))
    e2 = ev(2)
    C["dike_rebuild"] = abs(fl(re.search(r"treasury_change = (-?[\d.]+)", e2).group(1)))
    C["dike_rebuild_pts"] = fl(re.search(r"aral_pending = ([\d.]+)", e2).group(1))
    e4, e5, e7, e8, e9 = ev(4), ev(5), ev(7), ev(8), ev(9)
    S = {"accept": int(re.search(r"aral_sea\.4\.a\s+ai_chance = \{\s+base = (\d+)", e4).group(1)),
         "w": {ev: int(w) for w, ev in re.findall(r"(\d+) = \{ country_event = \{ id = aral_sea\.([678]) \}", e5)},
         "stall_days": int(re.search(r"days = (\d+)", e7).group(1)),
         "dead_days": int(re.search(r"aral_sib_dead days = (\d+)", e8).group(1)),
         "mult": fl(re.search(r"multiply_variable = \{ aral_sib_fee = ([\d.]+) \}", e9).group(1)),
         "cut_days": int(re.search(r"aral_sib_cut days = (\d+)", e9).group(1))}
    S["fee_current_limit"] = parse_siberian_fee_current_limit(e9)
    S["fee_cap"] = S["fee_current_limit"] * S["mult"]
    for v in ("canal", "pipe"):
        blk = re.search(r"has_country_flag = aral_sib_%s_done NOT = \{ has_country_flag = aral_sib_cut \} \}\s*set_temp_variable = \{ treasury_change = aral_sib_fee \}[\s\S]*?(\d+) = \{ country_event = \{ id = aral_sea\.9" % v, tick)
        dry = re.search(r"aral_sib_%s_done NOT = \{ has_country_flag = aral_sib_cut \} \} subtract_from_variable = \{ aral_dry_loss = (\d+)" % v, upd)
        drf = re.search(r"aral_sib_%s_done NOT = \{ has_country_flag = aral_sib_cut \} \} add_to_variable = \{ aral_drift = (-?[\d.]+)" % v, drift)
        S[v] = {"fee": abs(fl(re.search(r"aral_sib_fee = (-?[\d.]+)", sect(dec, "aral_sib_" + v)).group(1))), "p_lev": int(blk.group(1)) / 100.0, "dry": fl(dry.group(1)), "drift": fl(drf.group(1))}
    C["sib"] = S
    C["treasury0"] = float(treasury0)
    C["dyn_names"] = None
    D = {}
    cat = re.search(r"\n(\w+)\s*=\s*\{", "\n" + dec).group(1)
    body = sect(dec, cat)
    for m in re.finditer(r"(?m)^\t(aral_\w+)\s*=\s*\{", body):
        n = m.group(1)[5:]
        b = body[m.end():brace(body, m.end() - 1)]
        av, ce, rm = sect(b, "available"), sect(b, "complete_effect"), sect(b, "remove_effect")
        d = {"days": int(re.search(r"days_remove = (\d+)", b).group(1)),
             "pp": int(re.search(r"^\s*cost = (\d+)", b, re.M).group(1)) if re.search(r"^\s*cost = (\d+)", b, re.M) else 0,
             "tre": abs(fl(re.search(r"treasury_change = (-?[\d.]+)", ce).group(1))),
             "debt": fl(re.search(r"debt_change = (-?[\d.]+)", ce).group(1)) if "debt_change" in ce else 0.0,
             "relief": sum(fl(x) for x in re.findall(r"aral_relief = ([\d.]+)", rm)),
             "needs": re.findall(r"has_country_flag = aral_(\w+)_done", av),
             "excl": re.findall(r"NOT = \{ has_country_flag = aral_(\w+)_started", av),
             "dike": "set_country_flag = aral_dike\n" in rm or "set_country_flag = aral_dike " in rm}
        g = re.search(r"aral_sea_level > ([\d.]+)", av)
        d["gate"] = fl(g.group(1)) if g else 0.0
        d["clrdike"] = "clr_country_flag = aral_dike" in rm
        d["pending"] = sum(fl(x) for x in re.findall(r"aral_pending = ([\d.]+) tooltip", rm))
        D[n] = d
    return C, D


def level(C, r):
    return C["level_0"] + C["level_k"] * r


def run(C, D, income, pp_m, route, dike_policy, buy, rebuild, months, rng, trace=False, sib="no"):
    r = pend = relief = 0.0
    tre, pp, clock = C["treasury0"], 50.0, 0
    done, started, running, remaining = set(), set(), [], [n for n in PRIORITY if n in D and n != ("dam2" if route == "phase2" else "phase2")]
    if dike_policy == "no":
        remaining.remove("dike")
    dike = False
    spent_t = spent_d = 0.0
    dry = breaks = 0
    log, lv = [], []
    S = C["sib"]
    st, nxt, dead_until, cut_until, accepted = "idle", 0.0, -1.0, -1.0, False
    sibs = {"attempts": 0, "dead": 0, "cuts": 0, "online": None, "spent": 0.0, "fee": 0.0, "raises": 0}
    fee_now = 0.0
    for mth in range(months):
        day = mth * MONTH
        tre += income
        pp += pp_m
        for fin, n in [x for x in running if x[0] <= day]:
            running.remove((fin, n))
            d = D[n]
            done.add(n)
            if d["dike"]:
                if "kokaral" not in done:   # a dike that finishes after the dam changes nothing
                    pend += d["pending"]
                    dike = True
            else:
                pend += d["pending"]
            if d["clrdike"]:
                dike = False
            relief += d["relief"]
            if trace:
                log.append((mth, "done " + n))
        for n in list(remaining):
            d = D[n]
            if any(x not in done for x in d["needs"]) or any(x in started for x in d["excl"]):
                continue
            if d["gate"] and level(C, r) <= d["gate"]:
                continue
            if tre <= d["tre"] or pp < d["pp"]:
                continue
            tre -= d["tre"]
            pp -= d["pp"]
            spent_t += d["tre"]
            spent_d += d["debt"]
            started.add(n)
            running.append((day + d["days"], n))
            remaining.remove(n)
            if trace:
                log.append((mth, "start " + n))
        # Siberian water chain: request -> Russia answers -> commission verdicts -> build -> fees and price reviews
        if sib != "no":
            if st == "idle" and day >= dead_until and "ifas" in done and "loan" in done:
                d = D["sibaral"]
                if tre > d["tre"] and pp >= d["pp"]:
                    tre -= d["tre"]; pp -= d["pp"]; spent_t += d["tre"]; sibs["spent"] += d["tre"]; sibs["attempts"] += 1
                    accepted = rng.random() * 100 < S["accept"]
                    st, nxt = "request", day + d["days"]
            if st == "request" and day >= nxt:
                if accepted:
                    st, nxt = "study", day
                else:
                    st, dead_until = "idle", day + S["dead_days"]; sibs["dead"] += 1
            if st == "study" and day >= nxt:
                w6, w7, w8 = S["w"]["6"], S["w"]["7"], S["w"]["8"]
                x = rng.random() * (w6 + w7 + w8)
                if x < w6:
                    st = "ok"
                elif x < w6 + w7:
                    nxt = day + S["stall_days"]
                else:
                    st, dead_until = "idle", day + S["dead_days"]; sibs["dead"] += 1
            if st == "ok" and "kokaral" in done:
                d = D["sib_" + sib]
                if tre > d["tre"] and pp >= d["pp"]:
                    tre -= d["tre"]; pp -= d["pp"]; spent_t += d["tre"]; spent_d += d["debt"]; sibs["spent"] += d["tre"] + d["debt"]
                    st, nxt = "build", day + d["days"]
            if st == "build" and day >= nxt:
                st = "online"; sibs["online"] = mth; fee_now = S[sib]["fee"]
        on = sib != "no" and st == "online" and day >= cut_until
        # monthly tick (mirrors the caps in update_aral_sea, aral_calc_drift and aral_monthly_tick)
        cap = C["cap0"]
        for f, v in C["caps"]:
            if (f == "dike" and dike) or (f != "dike" and f in done):
                cap = v
        drift = C["drift0"] + sum(v for f, v in C["drift_adj"].items() if f in done) + (S[sib]["drift"] if on else 0.0)
        fill = min(pend, max(pend * C["fill_rate"], C["fill_min"])) if pend > 0.001 else 0.0
        if cap - r < 0.01:  # at the crest the inflow only spills over
            fill = 0.0
            if drift < 0:
                drift = 0.0
        r = r - drift + fill
        pend = max(0.0, pend - fill)
        clock += 1
        if clock > 11.99:
            clock = 0
            x = rng.random()
            if x < C["p_dry"]:
                dry += 1
                if buy and tre > C["dry_buy"] and pp >= C["dry_pp"]:
                    tre -= C["dry_buy"]
                    pp -= C["dry_pp"]
                    spent_t += C["dry_buy"]
                else:
                    r -= max(0.0, C["dry_base"] + sum(v for f, v in C["dry_adj"] if f in done) - (S[sib]["dry"] if on else 0.0))
            elif x < C["p_dry"] + C["p_wet"]:
                pend += C["wet_pts"]
            if on:
                tre -= fee_now; spent_t += fee_now; sibs["spent"] += fee_now
                if rng.random() < S[sib]["p_lev"]:  # Russia reopens the price: the player accepts while the fee stays under 0.15 bn a year
                    if fee_now > -S["fee_current_limit"]:
                        fee_now *= S["mult"]; sibs["raises"] += 1
                    else:
                        cut_until = day + S["cut_days"]; sibs["cuts"] += 1
                sibs["fee"] = fee_now
        if dike and rng.random() < C["p_dike"]:
            breaks += 1
            pend = 0.0          # the washed-out dike takes everything above the natural level
            r = min(r, 0.0)
            if rebuild and tre > C["dike_rebuild"]:
                tre -= C["dike_rebuild"]
                spent_t += C["dike_rebuild"]
                pend += C["dike_rebuild_pts"]
            else:
                dike = False
        cap = C["cap0"]
        for f, v in C["caps"]:
            if (f == "dike" and dike) or (f != "dike" and f in done):
                cap = v
        r = max(C["r_min"], min(cap, r))
        if cap - r < 0.01:
            pend = 0.0
        lv.append(level(C, r))
    return {"lv": lv, "dry": dry, "breaks": breaks, "spent": spent_t + spent_d, "log": log, "done": done, "sib": sibs}


def first(lv, L):
    for i, x in enumerate(lv):
        if x >= L - 1e-9:
            return i
    return None


def dt(start, m):
    d = start + datetime.timedelta(days=int(m * MONTH))
    return "%04d-%02d" % (d.year, d.month)


def pct(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))]


def parse_siberian_fee_current_limit(event_text):
    """Read the maximum current (negative) annual fee that allows a +50% price rise."""
    match = re.search(
        r"option\s*=\s*\{\s*name\s*=\s*aral_sea\.9\.a[\s\S]*?aral_sib_fee\s*>\s*(-?[\d.]+)",
        event_text,
    )
    if not match:
        raise ValueError("Siberian price-acceptance limit missing from aral_sea.9.a")
    limit = abs(float(match.group(1)))
    if limit <= 0:
        raise ValueError("Siberian price-acceptance limit must be positive")
    return limit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="mdredux")
    ap.add_argument("--income", type=float, help="treasury income per month, bn (not in the repo)")
    ap.add_argument("--treasury", type=float, default=0.245, help="starting treasury in bn (default: KAZ 2000 baseline)")
    ap.add_argument("--pp", type=float, default=45.0, help="political power per month")
    ap.add_argument("--route", choices=["phase2", "dam2"], default="phase2")
    ap.add_argument("--dike", choices=["yes", "no"], default="no")
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--months", type=int, default=420)
    ap.add_argument("--start", default="2000-01-01")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--once", action="store_true", help="print one run with its project log")
    ap.add_argument("--sib", choices=["no", "canal", "pipe"], default="no", help="follow the Siberian water chain with this technology")
    a = ap.parse_args()
    C, D = parse(a.root, a.treasury)
    start = datetime.date.fromisoformat(a.start)
    print("# Constants parsed from the code")
    print("level = %.0f + %.2f x restoration; %.1f m (restoration %.0f) .. %.1f m (%.0f)" % (C["level_0"], C["level_k"], level(C, C["r_min"]), C["r_min"], level(C, C["r_max"]), C["r_max"]))
    print("drift (negative = the river refills the sea, in decimetres per month): base %+.2f, improvements %s" % (C["drift0"], C["drift_adj"]))
    print("fill %.0f%% of pending per month (min %.1f); yearly river: dry %.0f%%, wet %.0f%% (+%g); dike washed out %.0f%%/month (the sea falls back to the natural level)" % (C["fill_rate"] * 100, C["fill_min"], C["p_dry"] * 100, C["p_wet"] * 100, C["wet_pts"], C["p_dike"] * 100))
    print("crest cap: %s (restoration, 1 point = 1 dm); dry year costs %g %s or pay %.2f bn + %g PP; start treasury %.3f bn" % (
        ", ".join("%s %g" % (f, v) for f, v in [("open", C["cap0"])] + C["caps"]), C["dry_base"], C["dry_adj"], C["dry_buy"], C["dry_pp"], C["treasury0"]))
    print("modifier coefficients per 1 deficit:", C["mods"])
    print("\n# Projects (parsed)")
    print("%-11s %5s %4s %5s %5s %6s %6s  needs / gate / excl" % ("decision", "days", "PP", "tre", "debt", "water", "relief"))
    for n, d in D.items():
        print("%-11s %5d %4d %5.2f %5.2f %6g %6g  %s" % (n, d["days"], d["pp"], d["tre"], d["debt"], d["pending"], d["relief"],
              ",".join(d["needs"]) + (" lvl>%g" % d["gate"] if d["gate"] else "") + (" excl(%s)" % ",".join(d["excl"]) if d["excl"] else "") + (" [dike]" if d["dike"] else "")))
    for route in ("phase2", "dam2"):
        skip = "dam2" if route == "phase2" else "phase2"
        water = min(sum(d["pending"] for k, d in D.items() if k not in (skip, "dike") and not k.startswith("sib")), dict(C["caps"])[route])
        tre = sum(d["tre"] for k, d in D.items() if k != skip and not k.startswith("sib"))
        dbt = sum(d["debt"] for k, d in D.items() if k != skip and not k.startswith("sib"))
        print("route %-6s: water %g -> ceiling %.1f m; relief %g; money %.2f treasury + %.2f debt = %.2f bn" % (route, water, level(C, water), sum(d["relief"] for d in D.values()), tre, dbt, tre + dbt))
    nothing = run(C, D, 0, 0, "phase2", "no", False, False, 600, random.Random(1))["lv"]
    print("do nothing: the level hovers around the natural level (lowest %.1f m after dry years, %.1f m at the end)" % (min(nothing), nothing[-1]))

    if a.once:
        res = run(C, D, a.income or 0.1, a.pp, a.route, a.dike, True, True, a.months, random.Random(a.seed), trace=True, sib=a.sib)
        for m, s in res["log"]:
            print("  %s month %3d  %s" % (dt(start, m), m, s))
        for m in (12, 24, 48, 72, 96, 144, 240, 360):
            if m < len(res["lv"]):
                print("  month %3d (%s): %.2f m" % (m, dt(start, m), res["lv"][m]))
        print("  dry years %d, dike washed out %d times, spent %.2f bn" % (res["dry"], res["breaks"], res["spent"]))
        if a.sib != "no":
            sb = res["sib"]
            print("  Siberian water (%s): requests %d, shelved %d times, online %s, fee rises %d, supplies cut %d, spent %.2f bn" % (a.sib, sb["attempts"], sb["dead"], dt(start, sb["online"]) if sb["online"] is not None else "never", sb["raises"], sb["cuts"], sb["spent"]))
        return
    print("\n# Monte Carlo, %d runs per row, start %s, +%g PP/month; player pays for dry-year releases and rebuilds the dike when affordable" % (a.runs, a.start, a.pp))
    print("%-7s %-6s %-5s | %-17s | %-8s %-8s %-8s | %-22s | %s" % ("income", "route", "dike", "42 m by 2008/12/20", "med 42 m", "med 44 m", "med 46 m", "level at the end p10/50/90", "dry yrs / dike breaks / spent bn / min level after 42 m"))
    incomes = [a.income] if a.income is not None else [0.005, 0.01, 0.02, 0.05]
    for inc in incomes:
        for route in ([a.route] if a.income is not None else ["phase2", "dam2"]):
            for dk in (["yes", "no"] if a.income is None else [a.dike]):
                rs = [run(C, D, inc, a.pp, route, dk, True, True, a.months, random.Random(a.seed * 1000 + i)) for i in range(a.runs)]
                f42 = [first(x["lv"], 42) for x in rs]
                f44 = [first(x["lv"], 44) for x in rs]
                f46 = [first(x["lv"], 46) for x in rs]
                by = lambda yr: 100.0 * sum(1 for f in f42 if f is not None and f <= (yr - start.year) * 12) / len(rs)
                med = lambda f: dt(start, statistics.median([x for x in f if x is not None])) if sum(1 for x in f if x is not None) > len(f) / 2 else "never"
                ends = [x["lv"][-1] for x in rs]
                mins = [min(x["lv"][f42[i]:]) for i, x in enumerate(rs) if f42[i] is not None]
                print("%-7g %-6s %-5s | %3.0f%% %3.0f%% %3.0f%%     | %-8s %-8s %-8s | %.1f / %.1f / %.1f m        | %.1f / %.1f / %.2f / %.1f m" % (
                    inc, route, dk, by(2008), by(2012), by(2020), med(f42), med(f44), med(f46),
                    pct(ends, .1), pct(ends, .5), pct(ends, .9),
                    statistics.mean(x["dry"] for x in rs), statistics.mean(x["breaks"] for x in rs), statistics.mean(x["spent"] for x in rs),
                    statistics.mean(mins) if mins else float("nan")))
    print("\n# Siberian water chain, %d runs per row (Phase II route, no dike; the player always follows the chain)" % a.runs)
    S = C["sib"]
    w = S["w"]; tot = sum(w.values())
    print("Russia studies the request: %d%% (never in war); verdict: feasible %d%%, more studies %d%% (+%d days), shelved %d%% (closed %d days)" % (S["accept"], 100 * w["6"] / tot, 100 * w["7"] / tot, S["stall_days"], 100 * w["8"] / tot, S["dead_days"]))
    print("Price review: +50%% is accepted only while the next annual fee stays at or below %.3f bn; otherwise supply is cut for %d days" % (S["fee_cap"], S["cut_days"]))
    print("%-7s %-6s | %-22s | %-9s | %-9s | %s" % ("income", "tech", "online by 2015/2025/2035", "median", "requests", "fee rises / supplies cut / yearly fee at the end bn / Siberian spend bn"))
    for inc in ([a.income] if a.income is not None else [0.02, 0.05, 0.1]):
        for tech in ("canal", "pipe"):
            rs = [run(C, D, inc, a.pp, "phase2", "no", True, True, a.months, random.Random(a.seed * 1000 + i), sib=tech) for i in range(a.runs)]
            on = [x["sib"]["online"] for x in rs]
            by = lambda yr: 100.0 * sum(1 for o in on if o is not None and o <= (yr - start.year) * 12) / len(rs)
            got = [o for o in on if o is not None]
            print("%-7g %-6s | %3.0f%% %3.0f%% %3.0f%%          | %-9s | %-9.1f | %.1f / %.1f / %.3f / %.2f" % (
                inc, tech, by(2015), by(2025), by(2035), dt(start, statistics.median(got)) if got else "never",
                statistics.mean(x["sib"]["attempts"] for x in rs), statistics.mean(x["sib"]["raises"] for x in rs), statistics.mean(x["sib"]["cuts"] for x in rs),
                statistics.mean(x["sib"]["fee"] for x in rs), statistics.mean(x["sib"]["spent"] for x in rs)))
    print("\n# Penalty at selected deficits (country level)")
    for deficit in (100, 60, 30, 20, 0):
        print("deficit %3d: " % deficit + ", ".join("%s %+.1f%%" % (k.replace("aral_mod_", ""), c * deficit * 100) for k, c in C["mods"].items()))


if __name__ == "__main__":
    main()
