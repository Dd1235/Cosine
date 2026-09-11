"""Independent small-instance checks for three reductions in review_c.json.
These are mathematical sanity checks, not full judge acceptance tests.
Run: python3 experiments/similarity-v1/review_c_checks.py
"""
from functools import lru_cache
from itertools import combinations
import random
import json
from pathlib import Path

rng = random.Random(20260911)
checks = {}
# Exhaustive pair replacement costs, independently enumerating resulting values.
count = 0
for k in range(1, 9):
    for a in range(k + 1):
        for b in range(k + 1):
            for target in range(k + 1):
                actual = min((a != x) + (b != y)
                             for x in range(k + 1) for y in range(k + 1)
                             if abs(x - y) == target)
                predicted = (0 if target == abs(a-b) else
                             1 if target <= max(a,b,k-a,k-b) else 2)
                assert actual == predicted, (k,a,b,target)
                count += 1
checks['symmetric_pair_cost_exhaustive_cases'] = count
# Compare the remainder/XOR characterization to literal arithmetic.
count = 0
for x in range(1, 301):
    for y in range(x, 301):
        condition = (x & y) == x and x.bit_length() == y.bit_length()
        assert (y % x == y ^ x) == condition, (x,y)
        count += 1
checks['remainder_xor_characterization_cases'] = count
# Literal circular pizza game versus independent sets of the required size.
count = 0
for length in (3,6,9,12):
    for _ in range(40):
        a = [rng.randint(1,20) for _ in range(length)]
        @lru_cache(None)
        def play(state):
            if not state:
                return 0
            best = 0
            for j, original_index in enumerate(state):
                gone = {(j-1)%len(state),j,(j+1)%len(state)}
                following = tuple(v for t,v in enumerate(state) if t not in gone)
                best = max(best,a[original_index]+play(following))
            return best
        oracle = play(tuple(range(length)))
        independent = max(sum(a[i] for i in chosen)
                          for chosen in combinations(range(length),length//3)
                          if all((i+1)%length not in chosen for i in chosen))
        assert oracle == independent, (a,oracle,independent)
        count += 1
checks['circular_pizza_game_vs_independent_selection_cases'] = count
# The claimed logarithmic Josephus recurrence versus literal queue elimination.
def kth(n,k):
    first = (n+1)//2
    if k <= first:
        answer = 2*k
        return answer if answer <= n else answer-n
    answer = kth(n//2,k-first)
    return 2*answer+1 if n%2 else 2*answer-1
count = 0
for n in range(1,201):
    alive = list(range(1,n+1)); pos = 0; order = []
    while alive:
        pos = (pos+1)%len(alive)
        order.append(alive.pop(pos))
    for k,expected in enumerate(order,1):
        assert kth(n,k) == expected
        count += 1
checks['josephus_halving_vs_literal_cases'] = count
p = Path(__file__).with_name('review_c.json')
d = json.loads(p.read_text())
assert len(d['reviews']) + len(d['unjudged']) == 993
assert len({(r['seed'],r['candidate']) for r in d['reviews']+d['unjudged']}) == 993
for r in d['reviews']:
    assert r['grade'] in range(4)
    assert all(x in d['task_evidence'] for x in r['evidence'])
print(json.dumps(checks,sort_keys=True))
