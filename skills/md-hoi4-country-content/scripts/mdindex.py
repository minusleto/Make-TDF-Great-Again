#!/usr/bin/env python3
"""MD/HOI4 mod index (focus/event/idea ids -> file:lines, loc keys). Env: MD_UPLOADS, MD_INDEX. Usage:
 kaz.py build            scan uploads, write index
 kaz.py ls [filter]      list files / ids matching regex
 kaz.py get ID [-n N]    print block(s) by id (focus/event/idea/scripted)
 kaz.py loc KEY|regex    print yml lines (+ which ids lack loc with 'missing')
 kaz.py find REGEX       grep with file:line (max 30)
 kaz.py check            cross-check: focus<->loc, event<->loc, dup keys
"""
import re,sys,os,json,glob
UP=os.environ.get("MD_UPLOADS","/mnt/user-data/uploads"); IDX=os.environ.get("MD_INDEX","/mnt/user-data/outputs/md_index.json")
def rd(p): return open(p,encoding='utf-8-sig',errors='replace').read().replace('\r','').split('\n')
def clean(n): return re.sub(r'^\d+_','',os.path.basename(n))
def build():
    I={'files':{},'ent':{},'loc':{}}
    best={}
    for p in glob.glob(UP+'/*'):
        if os.path.isdir(p): continue
        c=clean(p)
        if c not in best or os.path.getmtime(p)>os.path.getmtime(best[c]): best[c]=p
    for p in sorted(best.values()):
        L=rd(p); n=clean(p); I['files'][n]={'path':p,'lines':len(L)}
        if n.endswith('.yml'):
            for i,l in enumerate(L,1):
                m=re.match(r'^\s*([\w.\-]+):\d*\s*"(.*)"\s*$',l)
                if m: I['loc'].setdefault(m.group(1),[]).append([n,i])
            continue
        dep=0; stack=[]
        for i,l in enumerate(L,1):
            s=re.sub(r'#.*','',l)
            m=re.match(r'^\s*([\w.:]+)\s*=\s*\{',s)
            if m and dep<=3:
                stack.append((m.group(1),i,dep))
            for ch in s:
                if ch=='{': dep+=1
                elif ch=='}':
                    dep-=1
                    if stack and stack[-1][2]==dep:
                        k,st,sd=stack.pop()
                        blk=L[st-1:i]
                        txt='\n'.join(blk[:40])
                        idm=re.search(r'\bid\s*=\s*([\w.]+)',txt)
                        if k in('focus','country_event','news_event') and idm and (k=='focus' or sd==0):
                            I['ent'].setdefault(idm.group(1),[]).append([n,st,i,k])
                        elif k not in('focus','country_event','news_event') and sd<=(2 if 'ideas' in n else 1) and not re.match(r'(if|else|limit|trigger|available|modifier|allowed)$',k):
                            I['ent'].setdefault(k,[]).append([n,st,i,'blk'])
    json.dump(I,open(IDX,'w'))
    print({k:v['lines'] for k,v in I['files'].items()}, 'entities',len(I['ent']),'loc',len(I['loc']))
def ld():
    if not os.path.exists(IDX): build()
    return json.load(open(IDX))
def main():
    a=sys.argv[1:] or ['build']; c=a[0]
    if c=='build': return build()
    I=ld()
    if c=='ls':
        f=re.compile(a[1] if len(a)>1 else '.',re.I)
        for k,v in I['files'].items(): print(k,v['lines'])
        r=[k for k in I['ent'] if f.search(k)]
        print(len(r),'ids:',' '.join(r[:80]))
    elif c=='get':
        mx=int(a[a.index('-n')+1]) if '-n' in a else 120
        for f,s,e,k in I['ent'].get(a[1],[]):
            L=rd(I['files'][f]['path']); print(f'## {f}:{s}-{e} ({k})'); print('\n'.join(L[s-1:min(e,s-1+mx)]))
        if a[1] not in I['ent']: print('not found')
    elif c=='loc':
        r=re.compile(a[1]); n=0
        for k,v in I['loc'].items():
            if r.fullmatch(k) or (len(a[1])>3 and r.search(k) and a[1] not in I['loc']) or k==a[1]:
                for f,i in v:
                    print(f'{f}:{i}', rd(I['files'][f]['path'])[i-1].strip()[:300]); n+=1
            if n>=30: break
    elif c=='find':
        r=re.compile(a[1]); n=0
        for f,v in I['files'].items():
            for i,l in enumerate(rd(v['path']),1):
                if r.search(l): print(f'{f}:{i}: {l.strip()[:140]}'); n+=1
                if n>=30: return
    elif c=='check':
        dups=[k for k,v in I['loc'].items() if len(v)>1]
        print('dup loc keys:',len(dups),dups[:15])
        foc=[k for k,v in I['ent'].items() if any(x[3]=='focus' for x in v)]
        miss=[k for k in foc if k not in I['loc']]; missd=[k for k in foc if k+'_desc' not in I['loc']]
        print('focus',len(foc),'no title loc',len(miss),miss[:15],'| no desc',len(missd),missd[:15])
        ev=[k for k,v in I['ent'].items() if any(x[3] in('country_event','news_event') for x in v)]
        mt=[k for k in ev if k+'.t' not in I['loc'] or k+'.d' not in I['loc']]
        print('events',len(ev),'missing .t/.d',len(mt),mt[:15])
main()
