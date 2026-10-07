import json,shutil
from pathlib import Path
from fastapi import FastAPI,File,UploadFile,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .database import init_db,conn
from .models import Profile,Assessment
from .engine import load,extract,match
from .resume import text
from .hackathon_engine import insights as hackathon_insights
BASE=Path(__file__).resolve().parent.parent; FRONT=BASE/'frontend'; UP=BASE/'uploads'; UP.mkdir(exist_ok=True)
init_db(); app=FastAPI(title='SkillFit'); app.mount('/static',StaticFiles(directory=FRONT),name='static')
for route,file in {'/':'index.html','/passport':'passport.html','/resume':'resume.html','/dashboard':'dashboard.html','/jobs':'jobs.html','/gap':'gap.html','/assessment':'assessment.html','/reskill':'reskill.html','/whatif':'whatif.html'}.items():
    def make(f):
        return lambda: FileResponse(FRONT/f)
    app.get(route)(make(file))
@app.get('/api/health')
def health(): return {'ok':True}

@app.get('/api/hackathon/insights')
def hackathon_insights_api():
    try:
        return hackathon_insights()
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
@app.post('/api/profile')
def profile(p:Profile):
    c=conn(); cur=c.cursor(); cur.execute('INSERT INTO profiles(name,email,education,experience,career_break,location,work_mode,target_role,skills) VALUES(?,?,?,?,?,?,?,?,?)',(p.name,p.email,p.education,p.experience,p.career_break,p.location,p.work_mode,p.target_role,json.dumps(p.skills))); c.commit(); i=cur.lastrowid; c.close(); return {'id':i,**p.model_dump()}
def getp(i):
    c=conn(); r=c.execute('SELECT * FROM profiles WHERE id=?',(i,)).fetchone(); c.close()
    if not r: raise HTTPException(404,'Profile not found')
    d=dict(r); d['skills']=json.loads(d['skills'] or '[]'); return d
@app.get('/api/profile/{i}')
def profile_get(i:int): return getp(i)

@app.put('/api/profile/{i}')
def profile_update(i:int,p:Profile):
    current=getp(i)
    skills=p.skills if p.skills else current.get('skills',[])
    c=conn(); c.execute('UPDATE profiles SET name=?,email=?,education=?,experience=?,career_break=?,location=?,work_mode=?,target_role=?,skills=? WHERE id=?',(p.name,p.email,p.education,p.experience,p.career_break,p.location,p.work_mode,p.target_role,json.dumps(skills),i)); c.commit(); c.close()
    return {'id':i,**p.model_dump(),'skills':skills,'resume':current.get('resume')}
@app.post('/api/resume/{i}')
async def resume(i:int,file:UploadFile=File(...)):
    getp(i); ext=Path(file.filename).suffix.lower()
    if ext not in ['.pdf','.docx','.txt']: raise HTTPException(400,'Use PDF, DOCX or TXT')
    dest=UP/f'{i}_{Path(file.filename).name}';
    with dest.open('wb') as b: shutil.copyfileobj(file.file,b)
    skills=extract(text(dest)); c=conn(); c.execute('UPDATE profiles SET skills=?,resume=? WHERE id=?',(json.dumps(skills),file.filename,i)); c.commit(); c.close(); return {'skills':skills,'filename':file.filename}
@app.get('/api/matches/{i}')
def matches(i:int):
    p=getp(i); out=[]
    for j in load('jobs.json'): out.append({**j,**match(p,j)})
    return sorted(out,key=lambda x:x['match_score'],reverse=True)
@app.get('/api/gap/{i}/{jobid}')
def gap(i:int,jobid:int):
    p=getp(i); j=next((x for x in load('jobs.json') if x['id']==jobid),None)
    if not j: raise HTTPException(404,'Job not found')
    m=match(p,j); courses=[x for x in load('courses.json') if x['skill'].lower() in {s.lower() for s in m['missing_skills']}]
    return {'job':j,**m,'courses':courses}
@app.get('/api/whatif/{i}')
def whatif(i:int):
    # What-if paths should not disappear just because a role needs more than
    # two skills. Rank the nearest opportunity clusters and show the projected
    # fit after learning the missing skill bridge.
    p=getp(i); ps={x.lower() for x in p['skills']}; res=[]
    for j in load('jobs.json'):
        current=match(p,j)
        miss=[s for s in j['skills'] if s.lower() not in ps]
        have=[s for s in j['skills'] if s.lower() in ps]
        if not miss:
            continue
        # Keep a practical bridge for the MVP, but allow up to four skills so
        # the page remains useful for candidates with sparse profiles.
        if len(miss)>4:
            continue
        projected=dict(p)
        projected['skills']=p['skills'] + miss
        future=match(projected,j)
        res.append({
            'id':j['id'],
            'role':j['role'],
            'company':j['company'],
            'location':j['location'],
            'work_mode':j['work_mode'],
            'unlock':miss,
            'have':have,
            'current_match':current['match_score'],
            'projected_match':future['match_score'],
            'gain':round(future['match_score']-current['match_score'],1)
        })
    return sorted(res,key=lambda x:(len(x['unlock']),-x['gain']))[:6]
@app.post('/api/assessment')
def assessment(a:Assessment):
    getp(a.profile_id); c=conn(); c.execute('INSERT INTO assessments(profile_id,role,score) VALUES(?,?,?)',(a.profile_id,a.role,a.score)); c.commit(); c.close(); return {'saved':True}
