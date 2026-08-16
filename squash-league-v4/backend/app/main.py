import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field as PydanticField, validator
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Session, create_engine, select

# Configuration
DB = os.getenv("DATABASE_URL", "sqlite:///./squash.db")
SECRET = os.getenv("JWT_SECRET", "dev-secret")
engine = create_engine(DB, echo=False)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Constants
MATCH_STATUS_PENDING = "pending"
MATCH_STATUS_PLAYED = "played"
AVAILABILITY_PENDING = "pending"
AVAILABILITY_AVAILABLE = "available"
AVAILABILITY_UNAVAILABLE = "unavailable"
DEFAULT_ELO = 1500
DEFAULT_LEVEL = "Intermediate"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str = "PLAYER"


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = ""
    level: str = DEFAULT_LEVEL
    active: bool = True
    elo: int = DEFAULT_ELO
    user_id: Optional[int] = None


class Season(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = True


class LeaguePlayer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    season_id: int
    player_id: int


class Round(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    season_id: int
    number: int
    scheduled_date: Optional[str] = None
    deadline: Optional[str] = None


class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    round_id: int
    player_a: int
    player_b: int
    status: str = MATCH_STATUS_PENDING
    court: Optional[str] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    winner: Optional[int] = None
    a_sets: int = 0
    b_sets: int = 0


class MatchSet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int
    set_no: int
    a_points: int
    b_points: int


class EloHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int
    match_id: int
    old_elo: int
    new_elo: int


class Availability(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int
    player_id: int
    status: str = AVAILABILITY_PENDING
    proposed_date: Optional[str] = None
    proposed_time: Optional[str] = None

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    title: str
    body: str
    read: bool = False


# Pydantic Models for validation
class LoginRequest(BaseModel):
    email: str
    password: str

    @validator('email')
    def email_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Email is required')
        return v.lower()

    @validator('password')
    def password_not_empty(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Password must be at least 3 characters')
        return v


class CreatePlayerRequest(BaseModel):
    name: str = PydanticField(..., min_length=1)
    email: Optional[str] = ""
    level: str = DEFAULT_LEVEL


class ScheduleRoundRequest(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    court: Optional[str] = None
    deadline: Optional[str] = None


class MatchResultRequest(BaseModel):
    sets: List[str]

    @validator('sets')
    def validate_sets(cls, v):
        if not (3 <= len(v) <= 5):
            raise ValueError('3-5 sets required')
        try:
            parsed = [(int(x[0]), int(x[1])) for x in v]
            if any(a == b or a < 0 or b < 0 for a, b in parsed):
                raise ValueError('Invalid set scores')
            return v
        except (ValueError, IndexError, TypeError):
            raise ValueError('Invalid set format')


class AvailabilityRequest(BaseModel):
    status: str
    date: Optional[str] = None
    time: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        if v not in (AVAILABILITY_AVAILABLE, AVAILABILITY_UNAVAILABLE):
            raise ValueError(f'Status must be {AVAILABILITY_AVAILABLE} or {AVAILABILITY_UNAVAILABLE}')
        return v


class CreateSeasonRequest(BaseModel):
    name: str = PydanticField(..., min_length=1)

app = FastAPI(title="Squash League API", version="4.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session():
    """Database session dependency"""
    with Session(engine) as session:
        yield session


def get_current_user(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> User:
    """Verify JWT token and return authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        token = authorization[7:]
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify user has admin role"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def generate_round_robin_schedule(player_ids: List[int]) -> List[List[tuple]]:
    """Generate round-robin schedule using circle method.
    
    For odd number of players, adds a bye (-1).
    Returns list of rounds, each containing list of (player_a, player_b) tuples.
    """
    arr = list(player_ids)
    if len(arr) % 2:
        arr.append(-1)
    
    n = len(arr)
    rounds = []
    
    for _ in range(n - 1):
        pairs = []
        for i in range(n // 2):
            a, b = arr[i], arr[n - 1 - i]
            if a != -1 and b != -1:
                pairs.append((a, b))
        rounds.append(pairs)
        # Rotate: keep first fixed, move last to position 1, shift others
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    
    return rounds


def calculate_elo_change(player_a_elo: int, player_b_elo: int, player_a_win: bool, k: int = 32) -> int:
    """Calculate ELO change for player A.
    
    Args:
        player_a_elo: Current ELO of player A
        player_b_elo: Current ELO of player B
        player_a_win: True if player A won, False if player B won
        k: K-factor (default 32)
    
    Returns:
        ELO change for player A (can be negative)
    """
    expected_a = 1 / (1 + 10 ** ((player_b_elo - player_a_elo) / 400))
    score_a = 1 if player_a_win else 0
    return round(k * (score_a - expected_a))

@app.on_event("startup")
def startup_event():
    """Initialize database and create demo data on startup"""
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Create initial season if it doesn't exist
        if not session.exec(select(Season)).first():
            season = Season(name="Temporada 2026/27")
            session.add(season)
            session.commit()
            session.refresh(season)
            
            # Add demo players
            demo_players = [
                "Carlos García",
                "Diego Dávila",
                "Alex Martín",
                "Pedro López",
                "Luis Sánchez",
                "Juan Pérez"
            ]
            for i, name in enumerate(demo_players):
                player = Player(name=name, elo=DEFAULT_ELO + i * 5)
                session.add(player)
                session.commit()
                session.refresh(player)
                session.add(LeaguePlayer(season_id=season.id, player_id=player.id))
            
            # Create admin user if it doesn't exist
            if not session.exec(select(User)).first():
                admin_user = User(
                    email="admin@squash.local",
                    password_hash=pwd.hash("admin123"),
                    role="ADMIN"
                )
                session.add(admin_user)
            
            session.commit()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "4.0.0"}


@app.post("/auth/login")
def login(
    payload: LoginRequest,
    session: Session = Depends(get_session)
):
    """Authenticate user and return JWT token"""
    user = session.exec(
        select(User).where(User.email == payload.email)
    ).first()
    
    if not user or not pwd.verify(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = jwt.encode(
        {"sub": str(user.id), "role": user.role},
        SECRET,
        algorithm="HS256"
    )
    
    return {"access_token": token, "role": user.role}

@app.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current logged-in user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }


@app.get("/players")
def list_players(session: Session = Depends(get_session)):
    """List all active players"""
    return session.exec(
        select(Player).where(Player.active == True).order_by(Player.name)
    ).all()


@app.post("/players")
def create_player(
    payload: CreatePlayerRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new player (admin only)"""
    player = Player(
        name=payload.name,
        email=payload.email,
        level=payload.level
    )
    session.add(player)
    session.commit()
    session.refresh(player)
    
    # Add player to active season if it exists
    active_season = session.exec(
        select(Season).where(Season.active == True)
    ).first()
    
    if active_season:
        session.add(LeaguePlayer(season_id=active_season.id, player_id=player.id))
        session.commit()
    
    return player


@app.get("/admin/overview")
def get_admin_overview(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get admin dashboard overview"""
    seasons = session.exec(select(Season)).all()
    players = session.exec(select(Player)).all()
    matches = session.exec(select(Match)).all()
    
    return {
        "seasons": len(seasons),
        "players": len(players),
        "matches": len(matches),
        "played": sum(1 for m in matches if m.status == MATCH_STATUS_PLAYED),
        "pending": sum(1 for m in matches if m.status == MATCH_STATUS_PENDING)
    }

@app.get("/rounds")
def list_rounds(
    season_id: int = 1,
    session: Session = Depends(get_session)
):
    """List all rounds for a season"""
    return session.exec(
        select(Round)
        .where(Round.season_id == season_id)
        .order_by(Round.number)
    ).all()


@app.post("/rounds/{round_id}/schedule")
def schedule_round(
    round_id: int,
    payload: ScheduleRoundRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Schedule a round with date, time, and court (admin only)"""
    round_obj = session.get(Round, round_id)
    if not round_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Round not found"
        )
    
    round_obj.scheduled_date = payload.date
    round_obj.deadline = payload.deadline
    session.add(round_obj)
    
    # Update all matches in this round
    matches = session.exec(
        select(Match).where(Match.round_id == round_id)
    ).all()
    
    for match in matches:
        if payload.court:
            match.court = payload.court
        if payload.date:
            match.scheduled_date = payload.date
        if payload.time:
            match.scheduled_time = payload.time
        session.add(match)
    
    session.commit()
    return {"ok": True}


@app.get("/matches")
def list_matches(session: Session = Depends(get_session)):
    """List all matches with player names"""
    matches = session.exec(select(Match).order_by(Match.id)).all()
    
    # Load related data
    players = {p.id: p.name for p in session.exec(select(Player)).all()}
    rounds = {r.id: r.number for r in session.exec(select(Round)).all()}
    
    return [
        {
            "id": m.id,
            "round": rounds.get(m.round_id),
            "player_a": m.player_a,
            "player_a_name": players.get(m.player_a),
            "player_b": m.player_b,
            "player_b_name": players.get(m.player_b),
            "status": m.status,
            "a_sets": m.a_sets,
            "b_sets": m.b_sets,
            "court": m.court,
            "scheduled_date": m.scheduled_date,
            "scheduled_time": m.scheduled_time,
        }
        for m in matches
    ]


@app.get("/h2h/{player_a}/{player_b}")
def head_to_head(
    player_a: int,
    player_b: int,
    session: Session = Depends(get_session)
):
    """Get head-to-head record between two players"""
    matches = session.exec(
        select(Match).where(
            (
                (Match.player_a == player_a) & (Match.player_b == player_b)
            ) | (
                (Match.player_a == player_b) & (Match.player_b == player_a)
            )
        )
    ).all()
    
    played_matches = [m for m in matches if m.status == MATCH_STATUS_PLAYED]
    player_a_wins = sum(1 for m in played_matches if m.winner == player_a)
    player_b_wins = sum(1 for m in played_matches if m.winner == player_b)
    
    return {
        "matches": len(played_matches),
        "player_a_wins": player_a_wins,
        "player_b_wins": player_b_wins,
        "match_ids": [m.id for m in matches]
    }

@app.get("/seasons")
def list_seasons(session: Session = Depends(get_session)):
    """List all seasons ordered by most recent first"""
    return session.exec(
        select(Season).order_by(Season.id.desc())
    ).all()


@app.post("/seasons")
def create_season(
    payload: CreateSeasonRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new season (admin only)"""
    season = Season(name=payload.name)
    session.add(season)
    session.commit()
    session.refresh(season)
    return season


@app.post("/seasons/{season_id}/generate")
def generate_schedule(
    season_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Generate round-robin schedule for a season (admin only)"""
    season = session.get(Season, season_id)
    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found"
        )
    
    # Get all players in the season
    league_players = session.exec(
        select(LeaguePlayer).where(LeaguePlayer.season_id == season_id)
    ).all()
    player_ids = [lp.player_id for lp in league_players]
    
    if len(player_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 players required to generate schedule"
        )
    
    # Check if schedule already exists (idempotent)
    existing_round = session.exec(
        select(Round).where(Round.season_id == season_id)
    ).first()
    if existing_round:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Schedule already exists for this season"
        )
    
    # Generate schedule
    rounds = generate_round_robin_schedule(player_ids)
    
    for round_no, pairs in enumerate(rounds, 1):
        round_obj = Round(season_id=season_id, number=round_no)
        session.add(round_obj)
        session.commit()
        session.refresh(round_obj)
        
        for player_a, player_b in pairs:
            match = Match(
                round_id=round_obj.id,
                player_a=player_a,
                player_b=player_b
            )
            session.add(match)
    
    session.commit()
    
    total_matches = sum(len(pairs) for pairs in rounds)
    return {
        "rounds": len(rounds),
        "matches": total_matches
    }

@app.post("/matches/{match_id}/result")
def submit_match_result(
    match_id: int,
    payload: MatchResultRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Submit match result and update ELO ratings"""
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    if match.status == MATCH_STATUS_PLAYED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Match already played"
        )
    
    # Parse and validate set scores
    try:
        set_scores = [(int(s[0]), int(s[1])) for s in payload.sets]
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid set format"
        )
    
    # Validate set scores
    for a_points, b_points in set_scores:
        if a_points == b_points or a_points < 0 or b_points < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid set scores"
            )
    
    # Count set wins
    player_a_sets = sum(1 for a, b in set_scores if a > b)
    player_b_sets = sum(1 for a, b in set_scores if b > a)
    
    # Match must be won 3-0, 3-1, or 3-2
    if max(player_a_sets, player_b_sets) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match must finish 3-0, 3-1, or 3-2"
        )
    
    # Get players and calculate ELO change
    player_a = session.get(Player, match.player_a)
    player_b = session.get(Player, match.player_b)
    
    if not player_a or not player_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    player_a_won = player_a_sets > player_b_sets
    elo_change = calculate_elo_change(player_a.elo, player_b.elo, player_a_won)
    
    old_elo_a = player_a.elo
    old_elo_b = player_b.elo
    
    player_a.elo += elo_change
    player_b.elo -= elo_change
    
    # Delete old match sets if any
    old_sets = session.exec(
        select(MatchSet).where(MatchSet.match_id == match_id)
    ).all()
    for old_set in old_sets:
        session.delete(old_set)
    
    # Add new match sets
    for set_no, (a_points, b_points) in enumerate(set_scores, 1):
        match_set = MatchSet(
            match_id=match_id,
            set_no=set_no,
            a_points=a_points,
            b_points=b_points
        )
        session.add(match_set)
    
    # Update match
    match.status = MATCH_STATUS_PLAYED
    match.a_sets = player_a_sets
    match.b_sets = player_b_sets
    match.winner = match.player_a if player_a_won else match.player_b
    
    # Record ELO history
    elo_history_a = EloHistory(
        player_id=player_a.id,
        match_id=match_id,
        old_elo=old_elo_a,
        new_elo=player_a.elo
    )
    elo_history_b = EloHistory(
        player_id=player_b.id,
        match_id=match_id,
        old_elo=old_elo_b,
        new_elo=player_b.elo
    )
    
    session.add_all([player_a, player_b, match, elo_history_a, elo_history_b])
    session.commit()
    
    return {
        "winner": match.winner,
        "elo_change": elo_change,
        "a_elo": player_a.elo,
        "b_elo": player_b.elo
    }


@app.get("/me/matches")
def get_user_matches(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all matches for the current user"""
    player = session.exec(
        select(Player).where(Player.user_id == current_user.id)
    ).first()
    
    if not player:
        return []
    
    matches = session.exec(
        select(Match)
        .where((Match.player_a == player.id) | (Match.player_b == player.id))
        .order_by(Match.id)
    ).all()
    
    # Load related data
    players = {p.id: p.name for p in session.exec(select(Player)).all()}
    rounds = {r.id: r.number for r in session.exec(select(Round)).all()}
    
    return [
        {
            "id": m.id,
            "round": rounds.get(m.round_id),
            "opponent": players.get(
                m.player_b if m.player_a == player.id else m.player_a
            ),
            "home": m.player_a == player.id,
            "status": m.status,
            "score": f"{m.a_sets}-{m.b_sets}" if m.status == MATCH_STATUS_PLAYED else None,
        }
        for m in matches
    ]

@app.post("/matches/{match_id}/availability")
def submit_availability(
    match_id: int,
    payload: AvailabilityRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Submit player availability for a match"""
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    player = session.exec(
        select(Player).where(Player.user_id == current_user.id)
    ).first()
    
    if not player or player.id not in (match.player_a, match.player_b):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this match"
        )
    
    # Get or create availability record
    availability = session.exec(
        select(Availability).where(
            (Availability.match_id == match_id) &
            (Availability.player_id == player.id)
        )
    ).first()
    
    if not availability:
        availability = Availability(match_id=match_id, player_id=player.id)
    
    availability.status = payload.status
    availability.proposed_date = payload.date
    availability.proposed_time = payload.time
    
    session.add(availability)
    session.commit()
    session.refresh(availability)
    
    return availability


@app.get("/matches/{match_id}/availability")
def get_match_availability(
    match_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get availability records for a match"""
    return session.exec(
        select(Availability).where(Availability.match_id == match_id)
    ).all()


@app.get("/notifications")
def list_notifications(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all notifications for the current user"""
    return session.exec(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.id.desc())
    ).all()


@app.post("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mark a notification as read"""
    notification = session.get(Notification, notification_id)
    
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.read = True
    session.add(notification)
    session.commit()
    
    return {"ok": True}


@app.get("/standings")
def get_standings(
    season_id: int = 1,
    session: Session = Depends(get_session)
):
    """Get season standings with ELO ratings and statistics"""
    # Get all players in this season
    league_players = session.exec(
        select(LeaguePlayer).where(LeaguePlayer.season_id == season_id)
    ).all()
    
    player_ids = [lp.player_id for lp in league_players]
    players = {
        p.id: p 
        for p in session.exec(
            select(Player).where(Player.id.in_(player_ids))
        ).all()
    }
    
    # Initialize standings
    standings_dict = {
        player_id: {
            "id": player_id,
            "name": player.name,
            "elo": player.elo,
            "played": 0,
            "wins": 0,
            "losses": 0,
            "points": 0,
            "sets_for": 0,
            "sets_against": 0,
        }
        for player_id, player in players.items()
    }
    
    # Get all rounds in season
    season_rounds = session.exec(
        select(Round).where(Round.season_id == season_id)
    ).all()
    round_ids = {r.id for r in season_rounds}
    
    # Process all matches
    matches = session.exec(select(Match)).all()
    
    for match in matches:
        if match.round_id not in round_ids or match.status != MATCH_STATUS_PLAYED:
            continue
        
        player_a = match.player_a
        player_b = match.player_b
        
        # Update match stats
        standings_dict[player_a]["played"] += 1
        standings_dict[player_b]["played"] += 1
        
        standings_dict[player_a]["sets_for"] += match.a_sets
        standings_dict[player_a]["sets_against"] += match.b_sets
        standings_dict[player_b]["sets_for"] += match.b_sets
        standings_dict[player_b]["sets_against"] += match.a_sets
        
        # Update win/loss and points
        if match.winner == player_a:
            standings_dict[player_a]["wins"] += 1
            standings_dict[player_a]["points"] += 3
            standings_dict[player_b]["losses"] += 1
        else:
            standings_dict[player_b]["wins"] += 1
            standings_dict[player_b]["points"] += 3
            standings_dict[player_a]["losses"] += 1
    
    # Calculate set difference
    for standing in standings_dict.values():
        standing["diff"] = standing["sets_for"] - standing["sets_against"]
    
    # Sort by points, wins, set difference, sets for
    standings_list = sorted(
        standings_dict.values(),
        key=lambda x: (x["points"], x["wins"], x["diff"], x["sets_for"]),
        reverse=True
    )
    
    return standings_list


@app.get("/players/{player_id}/history")
def get_player_elo_history(
    player_id: int,
    session: Session = Depends(get_session)
):
    """Get ELO rating history for a player"""
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    history = session.exec(
        select(EloHistory)
        .where(EloHistory.player_id == player_id)
        .order_by(EloHistory.id)
    ).all()
    
    return {
        "player": player.name,
        "elo": player.elo,
        "history": history
    }
