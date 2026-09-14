"""Riddle of the Sphinx (ICPC WF 2022, kattis-riddleofthesphinx) -- verification.

Interactive.  Unknown nonnegative integers (A,B,C).  Exactly five query rounds;
a query is (a,b,c) with 0<=a,b,c<=10 and the reply is a*A+b*B+c*C, except that
AT MOST ONE of the five replies may be an arbitrary lie (0..1e5).  Then print
A,B,C.

Strategy under test (adaptive, uses 5 queries exactly):
  q1=(1,0,0)->x   q2=(0,1,0)->y   q3=(0,0,1)->z   q4=(1,1,1)->s
  if x+y+z == s:  no reply among q1..q4 can have been a lie, because changing
      any single one of those four numbers breaks the identity; answer (x,y,z)
      (a dummy 5th query (0,0,0) is still asked, since the format wants five).
  else: a lie has already been spent, so q5 is guaranteed truthful.  Exactly one
      of q1..q4 lied, so with d = s-(x+y+z) != 0 the truth is one of
        H4=(x,y,z)  [q4 lied],  H1=(x+d,y,z),  H2=(x,y+d,z),  H3=(x,y,z+d).
      Their values under q5=(1,2,3) are v0, v0+d, v0+2d, v0+3d -- four distinct
      numbers because d!=0 and the weights 1,2,3 are distinct and nonzero -- so
      the honest 5th reply names the truth uniquely.

The checker below is an EXHAUSTIVE ADAPTIVE ADVERSARY: for every hidden triple in
a range it tries every (which round to lie in) x (every wrong value from a large
set, including values that make the transcript look self-consistent), and it also
tries telling the truth throughout.
"""
import random

MAXR = 10**5

def solver(ask):
    """`ask(a,b,c)` performs one round and returns the sphinx's reply."""
    x = ask(1, 0, 0)
    y = ask(0, 1, 0)
    z = ask(0, 0, 1)
    s = ask(1, 1, 1)
    d = s - (x + y + z)
    if d == 0:
        ask(0, 0, 0)                      # fifth round is mandatory; ask a no-op
        return (x, y, z)
    v = ask(1, 2, 3)                      # guaranteed honest: the lie is spent
    cands = [(x, y, z), (x + d, y, z), (x, y + d, z), (x, y, z + d)]
    hits = [t for t in cands if t[0] + 2 * t[1] + 3 * t[2] == v]
    assert len(hits) == 1, (cands, v)     # separation argument, checked at runtime
    return hits[0]

class Judge:
    """One run: hidden triple, index of the lying round (None = fully honest),
    and the value it lies with."""
    def __init__(self, truth, lie_round, lie_value):
        self.truth = truth
        self.lie_round = lie_round
        self.lie_value = lie_value
        self.round = 0
        self.queries = []

    def ask(self, a, b, c):
        assert 0 <= a <= 10 and 0 <= b <= 10 and 0 <= c <= 10, ("illegal query", a, b, c)
        self.round += 1
        assert self.round <= 5, "more than five rounds"
        self.queries.append((a, b, c))
        A, B, C = self.truth
        true_r = a * A + b * B + c * C
        assert 0 <= true_r <= MAXR, ("reply out of the stated range", true_r)
        if self.round - 1 == self.lie_round:
            return self.lie_value
        return true_r

def run(truth, lie_round, lie_value):
    j = Judge(truth, lie_round, lie_value)
    out = solver(j.ask)
    assert j.round == 5, ("did not use exactly five rounds", j.round)
    return out, j

def lie_values_for(truth, lie_round, rnd):
    """Wrong values the sphinx could answer in that round (never the true one)."""
    a, b, c = [(1,0,0), (0,1,0), (0,0,1), (1,1,1), (1,2,3)][lie_round]
    A, B, C = truth
    t = a * A + b * B + c * C
    cands = {0, 1, t + 1, t + 2, t + 7, t - 1, t - 2, t - 7, 2 * t + 1, MAXR}
    cands |= {rnd.randint(0, 200) for _ in range(6)}
    cands |= {rnd.randint(0, MAXR) for _ in range(4)}
    return [v for v in cands if 0 <= v <= MAXR and v != t]

def exhaustive(limit, label, extra_triples=()):
    rnd = random.Random(20220000 + limit)
    runs = 0
    triples = [(A, B, C) for A in range(limit) for B in range(limit) for C in range(limit)]
    triples += list(extra_triples)
    for truth in triples:
        out, _ = run(truth, None, None)            # honest sphinx
        assert out == truth, ("honest run failed", truth, out)
        runs += 1
        for lie_round in range(5):
            for v in lie_values_for(truth, lie_round, rnd):
                out, j = run(truth, lie_round, v)
                assert out == truth, ("failed", truth, lie_round, v, out, j.queries)
                runs += 1
    print("  %-38s %7d transcripts, all recovered" % (label, runs))

def sanity_samples():
    """The two published interactions: the same hidden triples, every lie pattern."""
    print("sample hidden triples (from the published interactions)")
    for truth in [(4, 4, 4), (0, 42, 2024)]:
        rnd = random.Random(7)
        n = 0
        out, _ = run(truth, None, None); assert out == truth; n += 1
        for lr in range(5):
            for v in lie_values_for(truth, lr, rnd):
                out, j = run(truth, lr, v)
                assert out == truth, (truth, lr, v, out)
                n += 1
        print("  %-38s %7d transcripts, all recovered" % (str(truth), n))

def query_legality_note():
    """Largest reply our queries can provoke: (1,2,3) is the heaviest, so any
    triple the judge may hide (all its 10a+10b+10c <= 1e5 by the statement's
    reply bound) is safe for us."""
    print("query set used: (1,0,0) (0,1,0) (0,0,1) (1,1,1) and then (0,0,0) or (1,2,3)")
    print("  all coefficients in [0,10]; weight sum 6 <= 30, so replies stay in range")

if __name__ == "__main__":
    query_legality_note()
    print()
    sanity_samples()
    print()
    print("exhaustive adaptive adversary")
    exhaustive(5, "all triples in [0,4]^3")
    exhaustive(3, "all triples in [0,2]^3 (again, new rng)")
    big = [(0, 0, 0), (1000, 0, 0), (0, 3333, 0), (0, 0, 9999),
           (2022, 2023, 2024), (10**4, 1, 0), (7, 0, 3300)]
    rnd = random.Random(99)
    big += [tuple(rnd.randint(0, 3000) for _ in range(3)) for _ in range(40)]
    runs = 0
    for truth in big:
        out, _ = run(truth, None, None); assert out == truth; runs += 1
        for lr in range(5):
            for v in lie_values_for(truth, lr, rnd):
                out, j = run(truth, lr, v)
                assert out == truth, (truth, lr, v, out)
                runs += 1
    print("  %-38s %7d transcripts, all recovered" % ("large / random triples", runs))
    print()
    print("also checking the claimed impossibility that motivates query 5:")
    print("  if q5 repeated (1,1,1) instead, the lie 'q1 lied' and the lie 'q2 lied'")
    print("  produce identical transcripts, e.g. truth (1,5,0) vs (5,1,0):")
    for truth in [(1, 5, 0), (5, 1, 0)]:
        tr = [1 * truth[0], 1 * truth[1], 1 * truth[2],
              sum(truth), sum(truth)]
        print("    truth %-9s honest replies to (1,0,0)(0,1,0)(0,0,1)(1,1,1)(1,1,1) = %s"
              % (str(truth), tr))
    print("    a sphinx answering x=1,y=1,z=0,s=6,repeat=6 fits BOTH -> the fifth")
    print("    question must use distinct nonzero weights, as (1,2,3) does.")
    print()
    print("all checks passed")
