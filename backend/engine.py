import json,re
from pathlib import Path
D=Path(__file__).resolve().parent/'data'
def load(n): return json.loads((D/n).read_text(encoding='utf-8'))
def extract(text):
    t=re.sub(r'[^a-z0-9+#.\- ]+',' ',text.lower()); out=[]
    for s in load('skills.json'):
        for x in [s['name']]+s.get('aliases',[]):
            q=re.escape(x.lower())
            if re.search(r'(?<!\w)'+q+r'(?!\w)',t): out.append(s['name']); break
    return sorted(set(out))
def match(p,j):
    ps={x.lower() for x in p['skills']}; rs={x.lower() for x in j['skills']}; m=ps&rs; miss=rs-ps
    skill=100*len(m)/len(rs) if rs else 0
    exp=100 if j['experience']==0 else min(100,p['experience']/j['experience']*100)
    loc=100 if j['work_mode'].lower()=='remote' or p['location'].lower()==j['location'].lower() else 35
    wm=100 if p['work_mode'].lower()=='any' or p['work_mode'].lower()==j['work_mode'].lower() else 45
    target=(p.get('target_role') or '').lower()
    role_words={w for w in re.findall(r'[a-z0-9+#]+',target) if len(w)>2}
    job_words={w for w in re.findall(r'[a-z0-9+#]+',j['role'].lower()) if len(w)>2}
    role=100 if target and target==j['role'].lower() else (100*len(role_words & job_words)/len(role_words) if role_words else 50)
    score=.45*skill+.20*exp+.15*loc+.10*wm+.10*role
    return {'match_score':round(score,1),'skill_score':round(skill,1),'experience_score':round(exp,1),'location_score':round(loc,1),'work_score':round(wm,1),'role_score':round(role,1),'matched_skills':sorted(m),'missing_skills':sorted(miss)}
