from itertools import combinations
import sys
sys.path.insert(0,"backend")
from app.main import rr_schedule

def test_even_players():
    for n in [4,6,8,10,16]:
        ids=list(range(n))
        rounds=rr_schedule(ids)
        assert len(rounds)==n-1
        assert sum(len(r) for r in rounds)==n*(n-1)//2
        pairs=[tuple(sorted(p)) for r in rounds for p in r]
        assert len(set(pairs))==len(pairs)

def test_odd_players():
    for n in [3,5,7]:
        ids=list(range(n))
        rounds=rr_schedule(ids)
        assert len(rounds)==n
        pairs=[tuple(sorted(p)) for r in rounds for p in r]
        assert len(set(pairs))==len(pairs)
        assert len(pairs)==n*(n-1)//2
