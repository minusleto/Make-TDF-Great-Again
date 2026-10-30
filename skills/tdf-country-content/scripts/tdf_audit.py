#!/usr/bin/env python3
"""Статический аудит контента стран TDF/MDC по правилам скила tdf-country-content.

Запуск (из корня репозитория):
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py .            # таблица по всем странам
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --tags POR,KAZ
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --details KAZ   # списки ID по проверкам
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --json audit.json

Это статическая проверка текста. Она НЕ запускает игру и НЕ видит базовый мод
(GENERIC_* идеи, общие scripted effects, события чужих namespace): такие ссылки
помечаются как внешние, а не как ошибки.
"""
import argparse, json, os, re, statistics as st
from collections import Counter, defaultdict

BANNED = ['strengthen ties', 'mutual benefit', 'significant', 'foothold', 'valuable',
          'comprehensive', 'ensuring', 'foster', 'paving the way']
BANNED_WORD = re.compile(r'\bkey\b', re.I)
GENERIC_LABELS = {'good', 'great', 'nice', 'excellent', 'interesting', 'damn', 'yes', 'no', 'ok', 'okay',
                  'fantastic', 'wonderful', 'sad', 'sure', 'decline the proposal', 'decline', 'thanks'}
TAG_RE = r'(?:[A-Z]{3})'


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read()


def strip_comments(t):
    out = []
    for line in t.split('\n'):
        q, r = False, ''
        for ch in line:
            if ch == '"':
                q = not q
            if ch == '#' and not q:
                break
            r += ch
        out.append(r)
    return '\n'.join(out)


def match_brace(t, i):
    d, q = 0, False
    for j in range(i, len(t)):
        c = t[j]
        if c == '"':
            q = not q
        elif not q:
            if c == '{':
                d += 1
            elif c == '}':
                d -= 1
                if d == 0:
                    return j
    return -1


def blocks(t, name, top=False):
    pat = r'(?m)^' + ('' if top else r'[\t ]*') + name + r'\s*=\s*\{'
    for m in re.finditer(pat, t):
        s = m.end() - 1
        e = match_brace(t, s)
        if e > 0:
            yield t[s + 1:e]


def sub(body, name):
    m = re.search(r'(?:^|[\s{])' + name + r'\s*=\s*\{', body)
    if not m:
        return ''
    s = m.end() - 1
    e = match_brace(body, s)
    return body[s + 1:e] if e > 0 else ''


def parse_loc(path):
    d, dups = {}, []
    for line in read(path).split('\n'):
        m = re.match(r'^\s*([^\s:#]+):\d*\s*"(.*)"\s*(#.*)?\s*$', line.rstrip('\r'))
        if m:
            if m.group(1) in d:
                dups.append(m.group(1))
            d[m.group(1)] = m.group(2)
    return d, dups


def discover(repo):
    mod = os.path.join(repo, 'mdredux')
    nf, loc_dir, ev_dir = (os.path.join(mod, x) for x in ('common/national_focus', 'localisation/english', 'events'))
    locs = {f: parse_loc(os.path.join(loc_dir, f)) for f in os.listdir(loc_dir) if f.endswith('.yml')}
    countries = {}
    for f in sorted(os.listdir(nf)):
        if not f.endswith('_Focus_Tree.txt'):
            continue
        txt = strip_comments(read(os.path.join(nf, f)))
        m = re.search(r'tag\s*=\s*(' + TAG_RE + ')', txt[:2000])
        if not m:
            ids = re.findall(r'\bid\s*=\s*(' + TAG_RE + r')_', txt)
            tag = Counter(ids).most_common(1)[0][0] if ids else None
        else:
            tag = m.group(1)
        if not tag:
            continue
        best = max(locs, key=lambda lf: sum(1 for k in locs[lf][0] if k.startswith(tag + '_')))
        stem = f.replace('_Focus_Tree.txt', '')
        evf = next((x for x in os.listdir(ev_dir) if x.lower().split('.')[0] == stem.lower()), None)
        countries[tag] = dict(tree=os.path.join(nf, f), loc=best, events=os.path.join(ev_dir, evf) if evf else None)
    return countries, locs


def audit_country(tag, c, locs, all_loc, all_focus, defined_events):
    loc, dups = locs[c['loc']]
    raw = read(c['tree'])
    txt = strip_comments(raw)
    R = defaultdict(list)
    R['dup_loc_keys'] = dups[:200]
    R['space_indent_lines'] = sum(1 for l in raw.split('\n') if re.match(r'^ +\S', l))
    R['brace_balance'] = txt.count('{') - txt.count('}')
    foc = []
    for b in blocks(txt, 'focus'):
        m = re.search(r'\bid\s*=\s*([A-Za-z0-9_\.\-]+)', b)
        if m:
            foc.append((m.group(1), b))
    # ветки, скрытые через allow_branch = { always = no } (отключённый контент): loc к ним не обязателен
    def prereqs(b):
        return [pf for pb in re.findall(r'prerequisite\s*=\s*\{([^{}]*)\}', b) for pf in re.findall(r'focus\s*=\s*([A-Za-z0-9_\.\-]+)', pb)]
    fb_map = dict(foc)
    hidden = {f for f, b in foc if re.search(r'allow_branch\s*=\s*\{\s*always\s*=\s*no', b)}
    grew = True
    while grew:
        grew = False
        for f, b in foc:
            ps = prereqs(b)
            if f not in hidden and ps and all(p in hidden for p in ps):
                hidden.add(f)
                grew = True
    R['hidden_branch_focus'] = sorted(hidden)
    ids = Counter(i for i, _ in foc)
    R['dup_focus_ids'] = [k for k, v in ids.items() if v > 1]
    lens, own_foreign = [], Counter()
    for fid, b in foc:
        cr = sub(b, 'completion_reward')
        lg = re.search(r'log\s*=\s*"[^"]*[Ff]ocus\s+([A-Za-z0-9_\.\-]+)', cr)
        if cr and not lg:
            R['no_log'].append(fid)
        elif lg and lg.group(1) not in (fid, 'executed'):
            R['log_mismatch'].append((fid, lg.group(1)))
        for pb in re.findall(r'prerequisite\s*=\s*\{([^{}]*)\}', b):
            for pf in re.findall(r'focus\s*=\s*([A-Za-z0-9_\.\-]+)', pb):
                if pf not in all_focus:
                    R['prereq_missing'].append((fid, pf))
        for pf in re.findall(r'mutually_exclusive\s*=\s*\{[^{}]*focus\s*=\s*([A-Za-z0-9_\.\-]+)', b):
            if pf not in all_focus:
                R['mutex_missing'].append((fid, pf))
        m = re.search(r'relative_position_id\s*=\s*([A-Za-z0-9_\.\-]+)', b)
        if m and m.group(1) not in all_focus:
            R['relpos_missing'].append((fid, m.group(1)))
        d = loc.get(fid + '_desc')
        if fid not in hidden:
            if fid not in loc and fid not in all_loc:
                R['title_missing'].append(fid)
            if d is None and fid + '_desc' not in all_loc:
                R['desc_missing'].append(fid)
        t = loc.get(fid)
        if t and len(t) > 30:
            R['title_gt30'].append((fid, len(t)))
        if d:
            lens.append(len(d))
            if len(d) < 150:
                R['desc_lt150'].append((fid, len(d)))
            if len(d) > 340:
                R['desc_gt340'].append((fid, len(d)))
            low = d.lower()
            hit = [w for w in BANNED if w in low] + (['key'] if BANNED_WORD.search(d) else [])
            if hit:
                R['banned_phrase'].append((fid, ', '.join(hit)))
        if cr and not re.sub(r'log\s*=\s*"[^"]*"', '', cr).strip():
            R['empty_reward'].append(fid)
        for sf in re.findall(r'search_filters\s*=\s*\{([^{}]*)\}', b):
            for f_ in sf.split():
                if not f_.startswith('FOCUS_FILTER_'):
                    R['nonstandard_filter'].append((fid, f_))
        for a, b2 in re.findall(r'remove_idea\s*=\s*(\w+)\s+add_idea\s*=\s*(\w+)', cr):
            if a == b2:
                R['swap_same_idea'].append((fid, a))
        for tb in re.findall(r'add_tech_bonus\s*=\s*\{([^{}]*)\}', cr):
            if 'uses' not in tb:
                R['tech_bonus_no_uses'].append(fid)
        for ev in re.findall(r'country_event\s*=\s*\{\s*id\s*=\s*([A-Za-z0-9_\.\-]+)', cr):
            if c['events'] and ev not in defined_events:
                R['event_not_found'].append((fid, ev))
        for m in re.finditer(r'(?:add_ideas|swap_ideas|remove_idea|add_idea|has_idea|set_country_flag|has_country_flag)'
                             r'\s*=\s*\{?\s*(?:idea\s*=\s*|flag\s*=\s*)?((' + TAG_RE + r')_[A-Za-z0-9_]+)', cr):
            if m.group(2) != tag and m.group(2) in ('POR', 'SOV', 'SYR', 'ARM', 'ISR', 'POL', 'KAZ', 'BLR', 'HUN', 'SLO'):
                R['foreign_tag_ref'].append((fid, m.group(1)))
        if 'effect_tooltip' in cr and len(re.sub(r'\s', '', cr)) < 200 and cr.count('effect_tooltip') >= 1 \
                and not re.search(r'add_|set_|modify_|change_', re.sub(r'effect_tooltip\s*=\s*\{.*?\}', '', cr, flags=re.S)):
            R['tooltip_only_reward'].append(fid)
    R['n_focus'] = len(foc)
    R['desc_median'] = st.median(lens) if lens else 0
    # события
    if c['events']:
        et = strip_comments(read(c['events']))
        gen = 0
        for kind in ('country_event', 'news_event'):
            for b in blocks(et, kind, top=True):
                for ob in blocks(b, 'option'):
                    nm = re.search(r'name\s*=\s*([^\s]+)', ob)
                    lab = loc.get(nm.group(1)) if nm else None
                    if lab is None and nm and nm.group(1) not in all_loc:
                        R['event_option_label_missing'].append(nm.group(1))
                    if lab:
                        if lab.strip().rstrip('.!').lower() in GENERIC_LABELS:
                            R['event_generic_label'].append(lab)
                        elif len(lab) > 35:
                            R['event_label_gt35'].append(lab[:40])
                    if not re.search(r'\blog\s*=', ob):
                        R['event_option_no_log'].append(nm.group(1) if nm else '?')
    return R


ERRORS = ['dup_focus_ids', 'log_mismatch', 'no_log', 'prereq_missing', 'mutex_missing', 'relpos_missing', 'title_missing',
          'desc_missing', 'dup_loc_keys', 'foreign_tag_ref', 'swap_same_idea', 'event_not_found', 'event_option_label_missing', 'event_option_no_log']
WARNS = ['empty_reward', 'nonstandard_filter', 'hidden_branch_focus', 'tech_bonus_no_uses', 'title_gt30', 'desc_lt150', 'desc_gt340', 'banned_phrase', 'tooltip_only_reward', 'event_generic_label', 'event_label_gt35']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', nargs='?', default='.')
    ap.add_argument('--tags')
    ap.add_argument('--details')
    ap.add_argument('--json')
    a = ap.parse_args()
    countries, locs = discover(a.repo)
    all_loc = {}
    for d, _ in locs.values():
        all_loc.update(d)
    all_focus, defined_events = set(), set()
    for c in countries.values():
        for b in blocks(strip_comments(read(c['tree'])), 'focus'):
            m = re.search(r'\bid\s*=\s*([A-Za-z0-9_\.\-]+)', b)
            if m:
                all_focus.add(m.group(1))
        if c['events']:
            et = strip_comments(read(c['events']))
            for kind in ('country_event', 'news_event'):
                for b in blocks(et, kind, top=True):
                    m = re.search(r'\bid\s*=\s*([A-Za-z0-9_\.\-]+)', b)
                    if m:
                        defined_events.add(m.group(1))
    want = a.tags.split(',') if a.tags else sorted(countries)
    res = {t: audit_country(t, countries[t], locs, all_loc, all_focus, defined_events) for t in want if t in countries}
    cols = ['n_focus', 'desc_median'] + ERRORS + WARNS + ['space_indent_lines', 'brace_balance']
    short = lambda s: s.replace('_', ' ')[:11]
    print('\t'.join(['tag'] + [short(c) for c in cols]))
    for t, R in res.items():
        row = [t]
        for k in cols:
            v = R.get(k, 0)
            row.append(str(len(v)) if isinstance(v, list) else str(v))
        print('\t'.join(row))
    print('\nERROR-проверки: ' + ', '.join(ERRORS) + '\nWARN-проверки: ' + ', '.join(WARNS))
    print('event_not_found считается только для стран, у которых есть свой файл событий в репозитории.')
    if a.details:
        R = res[a.details]
        for k in ERRORS + WARNS:
            if R.get(k):
                print(f'\n[{k}] {len(R[k])}')
                for x in R[k][:60]:
                    print('  ', x)
    if a.json:
        json.dump({t: {k: v for k, v in R.items()} for t, R in res.items()}, open(a.json, 'w'), ensure_ascii=False, indent=1, default=list)


if __name__ == '__main__':
    main()
