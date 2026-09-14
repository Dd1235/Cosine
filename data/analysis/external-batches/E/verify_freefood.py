"""freefood: size of the union of at most 100 closed integer intervals in [1,365].

Intended solution is a 365-slot boolean stamp (or a difference array).  Checked
against a sort-and-merge interval union on random inputs.
"""
import random

def stamp(iv):                       # the intended O(N * 365) solution
    day = [False] * 366
    for s, t in iv:
        for d in range(s, t + 1):
            day[d] = True
    return sum(day)

def merge(iv):                       # independent: sort + merge
    tot, cur_s, cur_t = 0, None, None
    for s, t in sorted(iv):
        if cur_t is None or s > cur_t + 1:
            if cur_t is not None:
                tot += cur_t - cur_s + 1
            cur_s, cur_t = s, t
        else:
            cur_t = max(cur_t, t)
    if cur_t is not None:
        tot += cur_t - cur_s + 1
    return tot

def diff(iv):                        # independent: difference array + prefix sum
    d = [0] * 368
    for s, t in iv:
        d[s] += 1; d[t + 1] -= 1
    run = 0; tot = 0
    for i in range(1, 366):
        run += d[i]
        if run > 0: tot += 1
    return tot

# samples
assert stamp([(10,14),(13,17),(25,26)]) == 10
assert stamp([(1,365),(20,28)]) == 365
assert stamp([(29,29),(48,48),(102,102),(94,94)]) == 4
print("samples ok")

random.seed(1)
for _ in range(5000):
    n = random.randint(1, 100)
    hi = random.choice([5, 30, 365])        # force heavy overlap sometimes
    iv = []
    for _ in range(n):
        s = random.randint(1, hi); t = random.randint(s, hi)
        iv.append((s, t))
    a, b, c = stamp(iv), merge(iv), diff(iv)
    assert a == b == c, (iv, a, b, c)
print("ok: 5000 random cases, three methods agree")
