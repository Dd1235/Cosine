"""Verify the published solution for Kattis 'generatingnumbers' (2019 ICPC Asia Danang, G).

Problem: starting from 1, each instruction is either "add 1" or "permute the
decimal digits" (no leading zero).  For x <= 1e9 report the fewest instructions
that turn 1 into x.

Published solution (generatingnumbers.cpp), transcribed verbatim in `formula`:
let c be the number of digits of x.  Pay a fixed toll
    B(c) = sum_{i=1..c-1} (10*(i-1)+9) = 5*(c-1)^2 + 4*(c-1)
to walk from 1 up to 10^(c-1), then spend, for each digit of x, that digit's
value in increments plus one permutation to shove it out of the units place,
with three rebates: the leading 1 of 10^(c-1) already supplies one digit "1"
free, the last digit placed needs no closing permutation, and if x contains no
digit 1 at all the leading 1 is grown into x's first digit (one fewer
increment).  Numbers of the shape d000..0 are handled separately: they can only
be entered by incrementing from (d-1)999..9, and cost B(c) + (d-1) + 10*(c-1),
minus one more when d = 2.  x < 10 costs x-1.  O(1) time and space per query.

Ground truth here is a 0-1 BFS on the real state graph.  Increments only raise
a number and permutations preserve the digit count, so reaching a c-digit x
never needs a number with more than c digits; the search therefore runs over
[1, 10^c) with edges v -> v+1 (cost 1), v -> its digit-multiset class (cost 1),
and class -> every member (cost 0).

Checks: the three statement samples, then formula == BFS for EVERY x with up to
6 digits (999999 values).  Pass "7" on the command line to extend the sweep to
every 7-digit number as well (~30s, a few hundred MB); that run was done while
annotating and also reported zero mismatches.
"""
import sys
from collections import deque


def formula(xs):
    """Transcription of generatingnumbers.cpp; xs is the decimal string of x."""
    x = xs
    n = int(x)
    res = 0
    c = 1
    for i in range(1, 10):
        if n >= 10 ** i:
            res += 10 * (i - 1) + 9
        else:
            c = i
            break
    if n < 10:
        return n - 1
    special = 1
    for i in range(1, len(x)):
        if x[i] != '0':
            special = 0
    if special:
        if x[0] == '1':
            return res
        res += (ord(x[0]) - ord('1')) + 10 * (c - 1)
        if x[0] == '2':
            res -= 1
        return res
    has_one = 0
    for i in range(1, len(x)):
        if x[i] == '1':
            has_one = 1
            break
    s = "10000000000"
    used = 0
    for i in range(len(x)):
        if x[i] != s[i]:
            if x[i] == '1' and used == 0:
                used = 1
                continue
            res += (ord(x[i]) - 48) + 1
            if i == 0 and has_one == 0:
                res -= 1
            if i == len(x) - 1:
                res -= 1
        else:
            if i == 0:
                used = 1
    return res


def bfs(d):
    """0-1 BFS over [1, 10^d): v->v+1 (1), v->class (1), class->member (0)."""
    lim = 10 ** d
    inf = float('inf')
    gid = {}
    members = []
    gkey = [0] * lim
    for v in range(1, lim):
        k = ''.join(sorted(str(v)))
        g = gid.get(k)
        if g is None:
            g = len(gid)
            gid[k] = g
            members.append([])
        gkey[v] = g
        members[g].append(v)
    dist = [inf] * lim
    gdist = [inf] * len(members)
    dist[1] = 0
    dq = deque([1])                  # v >= 0: number; v < 0: class -v-1
    while dq:
        x = dq.popleft()
        if x >= 0:
            dv = dist[x]
            if x + 1 < lim and dv + 1 < dist[x + 1]:
                dist[x + 1] = dv + 1
                dq.append(x + 1)
            g = gkey[x]
            if dv + 1 < gdist[g]:
                gdist[g] = dv + 1
                dq.append(-g - 1)
        else:
            g = -x - 1
            dv = gdist[g]
            for u in members[g]:
                if dv < dist[u]:
                    dist[u] = dv
                    dq.appendleft(u)
    return dist


def main():
    top = 7 if len(sys.argv) > 1 and sys.argv[1] == "7" else 6
    for s, expected in (("5", 4), ("26", 17), ("843", 44)):
        got = formula(s)
        print("sample x=%-4s formula=%-3d expected=%-3d %s"
              % (s, got, expected, "OK" if got == expected else "MISMATCH"))
        assert got == expected

    for d in range(1, top + 1):
        dist = bfs(d)
        lo = 10 ** (d - 1) if d > 1 else 1
        bad = [(v, formula(str(v)), dist[v])
               for v in range(lo, 10 ** d) if formula(str(v)) != dist[v]]
        print("%d-digit numbers: %d checked against BFS, %d mismatches %s"
              % (d, 10 ** d - lo, len(bad), bad[:5]))
        assert not bad

    # the worst input the constraints allow, for the closed form only
    print("x=10^9 costs", formula("1000000000"),
          "= sum_{i=1..9}(10(i-1)+9); t <= 1000 queries, each O(1)")
    print("\nAll checks passed.")


main()
