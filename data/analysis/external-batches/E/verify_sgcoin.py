"""sgcoin: forge two consecutive blocks whose hashes have 7 trailing zeros.

H(prev, T, tok) = (v*7 + tok) mod p  with v = poly-hash_31(T) seeded at prev,
p = 1e9+7.  The token enters with coefficient 1, so for ANY fixed transaction
string T and ANY target value the token is forced:  tok = (target - 7v) mod p.
The only constraint is tok <= 1e9-1, i.e. tok must avoid the 7 residues
[1e9, 1e9+6]; targets are the 100 positive multiples of 1e7 that are <= p-1,
so a valid target always exists (and the first one almost always works).
"""
import random

P = 1000000007
LIM = 10**9            # token must be in [0, LIM-1]
T1, T2 = "charlie-pays-to-eve-9-sg-coins", "icpc-sg-2018-at-nus"

def H(prev, t, tok):
    v = prev
    for ch in t:
        v = (v * 31 + ord(ch)) % P
    return (v * 7 + tok) % P

def forge(prev, t):
    v = prev
    for ch in t:
        v = (v * 31 + ord(ch)) % P
    for k in range(1, 101):                       # targets 1e7 .. 1e9
        target = k * 10**7
        tok = (target - 7 * v) % P
        if tok < LIM:
            return tok, target
    raise AssertionError("no token")

def solve(h0):
    tok1, h1 = forge(h0, T1)
    tok2, h2 = forge(h1, T2)
    return (T1, tok1, h1), (T2, tok2, h2)

# the statement's worked example
assert H(140000000, T1, 218216710) == 930000000
assert H(930000000, T2, 620658977) == 730000000
assert H(140000000, "alice-pays-bob-3-sg-coins", 606969470) == 990000000
assert H(140000000, "alice-pays-bob-3-sg-coins", 306969470) == 690000000
print("statement's own examples reproduce")

random.seed(3)
cases = [0, 10**7, 140000000, 10**9] + [random.randrange(0, 101) * 10**7 for _ in range(2000)]
worst = 0
for h0 in cases:
    (t1, k1, h1), (t2, k2, h2) = solve(h0)
    assert 0 <= k1 < LIM and 0 <= k2 < LIM
    assert H(h0, t1, k1) == h1 and H(h1, t2, k2) == h2
    for h in (h1, h2):
        assert h > 0 and h % 10**7 == 0 and h <= P - 1
    assert all(c.islower() or c.isdigit() or c == '-' for c in t1 + t2)
    assert 0 < len(t1) <= 100 and 0 < len(t2) <= 100
    worst = max(worst, h1 // 10**7, h2 // 10**7)
print("ok: %d chains forged, every block valid; worst target index used = %d"
      % (len(cases), worst))
