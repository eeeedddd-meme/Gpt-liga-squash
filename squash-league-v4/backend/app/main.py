import os
from itertools import combinations
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Session, create_engine, select

DB = os.getenv("DATABASE_URL", "sqlite:///./squash.db")
SECRET = os.getenv("JWT_SECRET", "dev-secret")
engine = create_engine(DB, echo=False)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str = "PLAYER"

class Player(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    name: str
    email: str=""
    level: str="Intermediate"
    active: bool=True
    elo: int=1500
    user_id: Optional[int]=None

class Season(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    name: str
    active: bool=True

class LeaguePlayer(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    season_id: int
    player_id: int

class Round(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    season_id: int
    number: int
    scheduled_date: Optional[str]=None
    deadline: Optional[str]=None

class Match(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    round_id: int
    player_a: int
    player_b: int
    status: str="pending"
    court: Optional[str]=None
    scheduled_date: Optional[str]=None
    scheduled_time: Optional[str]=None
    winner: Optional[int]=None
    a_sets: int=0
    b_sets: int=0

class MatchSet(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    match_id: int
    set_no: int
    a_points: int
    b_points: int

class EloHistory(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    player_id: int
    match_id: int
    old_elo: int
    new_elo: int


class Availability(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    match_id: int
    player_id: int
    status: str="pending"  # pending / available / unavailable
    proposed_date: Optional[str]=None
    proposed_time: Optional[str]=None

class Notification(SQLModel, table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    user_id: int
    title: str
    body: str
    read: bool=False

app=FastAPI(title="Squash League API",version="3.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000"],allow_credentials=True,
                   allow_methods=["*"],allow_headers=["*"])

def session():
    with Session(engine) as s: yield s

def auth(authorization: Optional[str]=Header(None), s:Session=Depends(session)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401,"Authentication required")
    try: payload=jwt.decode(authorization[7:],SECRET,algorithms=["HS256"])
    except JWTError: raise HTTPException(401,"Invalid token")
    u=s.get(User,int(payload["sub"]))
    if not u: raise HTTPException(401,"User not found")
    return u

def admin(u=Depends(auth)):
    if u.role!="ADMIN": raise HTTPException(403,"Admin required")
    return u

def rr_schedule(ids):
    # Circle method. For odd N, add a bye (-1).
    arr=list(ids)
    if len(arr)%2: arr.append(-1)
    n=len(arr); rounds=[]
    for r in range(n-1):
        pairs=[]
        for i in range(n//2):
            a,b=arr[i],arr[n-1-i]
            if a!=-1 and b!=-1: pairs.append((a,b))
        rounds.append(pairs)
        arr=[arr[0]]+[arr[-1]]+arr[1:-1]
    return rounds

@app.on_event("startup")
def startup():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        if not s.exec(select(Season)).first():
            season=Season(name="Temporada 2026/27"); s.add(season); s.commit(); s.refresh(season)
            demo=["Carlos García","Diego Dávila","Alex Martín","Pedro López","Luis Sánchez","Juan Pérez"]
            for i,name in enumerate(demo):
                p=Player(name=name,elo=1500+i*5); s.add(p); s.commit(); s.refresh(p)
                s.add(LeaguePlayer(season_id=season.id,player_id=p.id))
            if not s.exec(select(User)).first():
                s.add(User(email="admin@squash.local",password_hash=pwd.hash("admin123"),role="ADMIN"))
            s.commit()

@app.get("/health")
def health(): return {"status":"ok","version":"3.0.0"}

@app.post("/auth/login")
def login(payload:dict,s:Session=Depends(session)):
    u=s.exec(select(User).where(User.email==payload.get("email",""))).first()
    if not u or not pwd.verify(payload.get("password",""),u.password_hash):
        raise HTTPException(401,"Invalid credentials")
    token=jwt.encode({"sub":str(u.id),"role":u.role},SECRET,algorithm="HS256")
    return {"access_token":token,"role":u.role}

@app.get("/me")
def me(u=Depends(auth)): return {"id":u.id,"email":u.email,"role":u.role}

@app.get("/players")
def players(s:Session=Depends(session)): return s.exec(select(Player).order_by(Player.name)).all()

@app.post("/players")
def create_player(payload:dict,u=Depends(admin),s:Session=Depends(session)):
    name=str(payload.get("name","")).strip()
    if not name: raise HTTPException(400,"name required")
    p=Player(name=name,email=payload.get("email",""),level=payload.get("level","Intermediate"))
    s.add(p); s.commit(); s.refresh(p)
    season=s.exec(select(Season).where(Season.active==True)).first()
    if season: s.add(LeaguePlayer(season_id=season.id,player_id=p.id)); s.commit()
    return p


@app.get("/admin/overview")
def admin_overview(u=Depends(admin),s:Session=Depends(session)):
    seasons=s.exec(select(Season)).all()
    players=s.exec(select(Player)).all()
    matches=s.exec(select(Match)).all()
    return {"seasons":len(seasons),"players":len(players),"matches":len(matches),
            "played":sum(m.status=="played" for m in matches),
            "pending":sum(m.status=="pending" for m in matches)}

@app.post("/rounds/{round_id}/schedule")
def schedule_round(round_id:int,payload:dict,u=Depends(admin),s:Session=Depends(session)):
    r=s.get(Round,round_id)
    if not r: raise HTTPException(404,"round not found")
    r.scheduled_date=payload.get("date")
    r.deadline=payload.get("deadline")
    s.add(r)
    for m in s.exec(select(Match).where(Match.round_id==round_id)).all():
        if payload.get("court"): m.court=payload["court"]
        if payload.get("date"): m.scheduled_date=payload["date"]
        if payload.get("time"): m.scheduled_time=payload["time"]
        s.add(m)
    s.commit()
    return {"ok":True}

@app.get("/rounds")
def rounds(season_id:int=1,s:Session=Depends(session)):
    return s.exec(select(Round).where(Round.season_id==season_id).order_by(Round.number)).all()

@app.get("/h2h/{player_a}/{player_b}")
def h2h(player_a:int,player_b:int,s:Session=Depends(session)):
    ms=s.exec(select(Match).where(
        ((Match.player_a==player_a)&(Match.player_b==player_b))|
        ((Match.player_a==player_b)&(Match.player_b==player_a))
    )).all()
    a_wins=sum(m.status=="played" and m.winner==player_a for m in ms)
    b_wins=sum(m.status=="played" and m.winner==player_b for m in ms)
    return {"matches":len([m for m in ms if m.status=="played"]),
            "player_a_wins":a_wins,"player_b_wins":b_wins,
            "match_ids":[m.id for m in ms]}

@app.get("/seasons")
def seasons(s:Session=Depends(session)): return s.exec(select(Season).order_by(Season.id.desc())).all()

@app.post("/seasons")
def create_season(payload:dict,u=Depends(admin),s:Session=Depends(session)):
    name=str(payload.get("name","")).strip()
    if not name: raise HTTPException(400,"name required")
    season=Season(name=name); s.add(season); s.commit(); s.refresh(season); return season

@app.post("/seasons/{season_id}/generate")
def generate(season_id:int,u=Depends(admin),s:Session=Depends(session)):
    season=s.get(Season,season_id)
    if not season: raise HTTPException(404,"season not found")
    ids=[x.player_id for x in s.exec(select(LeaguePlayer).where(LeaguePlayer.season_id==season_id)).all()]
    if len(ids)<2: raise HTTPException(400,"at least 2 players")
    # Idempotent: don't generate a second calendar.
    if s.exec(select(Round).where(Round.season_id==season_id)).first():
        raise HTTPException(409,"schedule already exists")
    rounds=rr_schedule(ids)
    for no,pairs in enumerate(rounds,1):
        r=Round(season_id=season_id,number=no); s.add(r); s.commit(); s.refresh(r)
        for a,b in pairs: s.add(Match(round_id=r.id,player_a=a,player_b=b))
    s.commit()
    return {"rounds":len(rounds),"matches":sum(map(len,rounds))}

@app.get("/matches")
def matches(s:Session=Depends(session)):
    ms=s.exec(select(Match).order_by(Match.id)).all()
    ps={p.id:p.name for p in s.exec(select(Player)).all()}
    rs={r.id:r.number for r in s.exec(select(Round)).all()}
    return [{"id":m.id,"round":rs[m.round_id],"player_a":m.player_a,"player_a_name":ps[m.player_a],
             "player_b":m.player_b,"player_b_name":ps[m.player_b],"status":m.status,
             "a_sets":m.a_sets,"b_sets":m.b_sets,"court":m.court,
             "scheduled_date":m.scheduled_date,"scheduled_time":m.scheduled_time} for m in ms]

def elo_change(ra,rb,sa,k=32):
    ea=1/(1+10**((rb-ra)/400))
    return round(k*(sa-ea))

@app.post("/matches/{match_id}/result")
def result(match_id:int,payload:dict,u=Depends(auth),s:Session=Depends(session)):
    m=s.get(Match,match_id)
    if not m: raise HTTPException(404,"match not found")
    scores=payload.get("sets",[])
    if not 3<=len(scores)<=5: raise HTTPException(400,"3-5 sets required")
    parsed=[(int(x[0]),int(x[1])) for x in scores]
    if any(a==b or a<0 or b<0 for a,b in parsed): raise HTTPException(400,"invalid set")
    aw=sum(a>b for a,b in parsed); bw=sum(b>a for a,b in parsed)
    if max(aw,bw)!=3: raise HTTPException(400,"match must finish 3-0, 3-1 or 3-2")
    if m.status=="played": raise HTTPException(409,"match already played")
    pa,pb=s.get(Player,m.player_a),s.get(Player,m.player_b)
    olda,oldb=pa.elo,pb.elo
    sa=1 if aw>bw else 0
    d=elo_change(olda,oldb,sa)
    pa.elo+=d; pb.elo-=d
    for old in s.exec(select(MatchSet).where(MatchSet.match_id==match_id)).all(): s.delete(old)
    for i,(a,b) in enumerate(parsed,1): s.add(MatchSet(match_id=match_id,set_no=i,a_points=a,b_points=b))
    m.status="played"; m.a_sets=aw; m.b_sets=bw; m.winner=m.player_a if sa else m.player_b
    s.add_all([pa,pb,m,EloHistory(player_id=pa.id,match_id=m.id,old_elo=olda,new_elo=pa.elo),
               EloHistory(player_id=pb.id,match_id=m.id,old_elo=oldb,new_elo=pb.elo)])
    s.commit()
    return {"winner":m.winner,"elo_change":d,"a_elo":pa.elo,"b_elo":pb.elo}


@app.get("/me/matches")
def my_matches(u=Depends(auth),s:Session=Depends(session)):
    p=s.exec(select(Player).where(Player.user_id==u.id)).first()
    if not p:
        return []
    ms=s.exec(select(Match).where((Match.player_a==p.id)|(Match.player_b==p.id)).order_by(Match.id)).all()
    ps={x.id:x.name for x in s.exec(select(Player)).all()}
    rs={r.id:r.number for r in s.exec(select(Round)).all()}
    return [{"id":m.id,"round":rs.get(m.round_id),"opponent":ps.get(m.player_b if m.player_a==p.id else m.player_a),
             "home":m.player_a==p.id,"status":m.status,"score":f"{m.a_sets}-{m.b_sets}" if m.status=="played" else None} for m in ms]

@app.post("/matches/{match_id}/availability")
def availability(match_id:int,payload:dict,u=Depends(auth),s:Session=Depends(session)):
    m=s.get(Match,match_id)
    if not m: raise HTTPException(404,"match not found")
    p=s.exec(select(Player).where(Player.user_id==u.id)).first()
    if not p or p.id not in (m.player_a,m.player_b): raise HTTPException(403,"not a participant")
    status=payload.get("status")
    if status not in ("available","unavailable"): raise HTTPException(400,"invalid status")
    a=s.exec(select(Availability).where(Availability.match_id==match_id,Availability.player_id==p.id)).first()
    if not a:
        a=Availability(match_id=match_id,player_id=p.id)
    a.status=status
    a.proposed_date=payload.get("date")
    a.proposed_time=payload.get("time")
    s.add(a); s.commit(); s.refresh(a)
    return a

@app.get("/matches/{match_id}/availability")
def match_availability(match_id:int,u=Depends(auth),s:Session=Depends(session)):
    return s.exec(select(Availability).where(Availability.match_id==match_id)).all()

@app.get("/notifications")
def notifications(u=Depends(auth),s:Session=Depends(session)):
    return s.exec(select(Notification).where(Notification.user_id==u.id).order_by(Notification.id.desc())).all()

@app.post("/notifications/{notification_id}/read")
def notification_read(notification_id:int,u=Depends(auth),s:Session=Depends(session)):
    n=s.get(Notification,notification_id)
    if not n or n.user_id!=u.id: raise HTTPException(404,"notification not found")
    n.read=True; s.add(n); s.commit(); return {"ok":True}

@app.get("/standings")
def standings(season_id:int=1,s:Session=Depends(session)):
    ids=[x.player_id for x in s.exec(select(LeaguePlayer).where(LeaguePlayer.season_id==season_id)).all()]
    ps={p.id:p for p in s.exec(select(Player).where(Player.id.in_(ids))).all()}
    rows={i:{"id":i,"name":p.name,"elo":p.elo,"played":0,"wins":0,"losses":0,"points":0,"sets_for":0,"sets_against":0} for i,p in ps.items()}
    rids=[r.id for r in s.exec(select(Round).where(Round.season_id==season_id)).all()]
    for m in s.exec(select(Match)).all():
        if m.round_id not in rids or m.status!="played": continue
        a,b=m.player_a,m.player_b; rows[a]["played"]+=1; rows[b]["played"]+=1
        rows[a]["sets_for"]+=m.a_sets; rows[a]["sets_against"]+=m.b_sets
        rows[b]["sets_for"]+=m.b_sets; rows[b]["sets_against"]+=m.a_sets
        if m.winner==a: rows[a]["wins"]+=1; rows[a]["points"]+=3; rows[b]["losses"]+=1
        else: rows[b]["wins"]+=1; rows[b]["points"]+=3; rows[a]["losses"]+=1
    for x in rows.values(): x["diff"]=x["sets_for"]-x["sets_against"]
    return sorted(rows.values(),key=lambda x:(x["points"],x["wins"],x["diff"],x["sets_for"]),reverse=True)

@app.get("/players/{player_id}/history")
def history(player_id:int,s:Session=Depends(session)):
    ps=s.get(Player,player_id)
    if not ps: raise HTTPException(404,"player not found")
    h=s.exec(select(EloHistory).where(EloHistory.player_id==player_id).order_by(EloHistory.id)).all()
    return {"player":ps.name,"elo":ps.elo,"history":h}
