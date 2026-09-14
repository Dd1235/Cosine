"""codechef-productpos : "Product Positive" (CodeChef PRODUCTPOS).

Game on an array A of +-1.  A move picks a contiguous subarray whose product is
+1 (an EVEN number of -1s, possibly zero) and deletes it.  The player unable to
move loses; Alice moves first.  Print the winner, and for Alice a winning first
move (L, R).

Brute force (memoised over every reachable array) established the P-positions:

    the empty array, and exactly the arrays  1^k (-1) 1^k   (k >= 0),
    i.e. one single -1 sitting in the exact centre of an otherwise all-+1 array.

So the loser-to-move set is tiny and the solution is a pure construction:

  * m (= #(-1)) even  -> delete the whole array (1, n); the product is +1 and the
    opponent faces the empty array.
  * m odd  -> the move must leave exactly one -1, centred.  Parity is invariant
    (every move deletes an even number of -1s) so this is the only target.
    Keep either the first -1 (q1) or the last (qm) and delete the contiguous
    block holding the other m-1 of them, trimming +1s so the survivor is centred.
    With a = #(+1) before q1, b = #(+1) after qm, g = gap of +1s between q1,q2
    and h = gap between q_{m-1},qm, keeping q1 needs a <= g + b and keeping qm
    needs b <= h + a; both can fail only if 0 > g + h, so one always applies
    unless a == b and g,h are absent (m == 1) -- which is precisely the
    P-position where Bob wins.

O(n) per test, O(sum N) = 2e5 overall.
"""
import sys, random

# ------------------------------------------------------------------ brute force
sys.setrecursionlimit(100000)
memo = {}

def moves(a):
    n = len(a); out = []
    for l in range(n):
        neg = 0
        for r in range(l, n):
            if a[r] == -1: neg += 1
            if neg % 2 == 0: out.append((l, r))
    return out

def win(a):
    if a in memo: return memo[a]
    res = False
    for (l, r) in moves(a):
        if not win(a[:l] + a[r + 1:]):
            res = True; break
    memo[a] = res
    return res

# ------------------------------------------------------------------ solution
def solve(a):
    """a: list of +-1 (1-indexed conceptually). -> ('Bob', None) | ('Alice',(L,R))"""
    n = len(a)
    q = [i + 1 for i, x in enumerate(a) if x == -1]     # 1-based -1 positions
    m = len(q)

    if m % 2 == 0:                       # includes m == 0
        return ('Alice', (1, n))

    aa = q[0] - 1                        # +1s strictly before the first -1
    bb = n - q[-1]                       # +1s strictly after the last -1
    if m == 1:
        g = h = 0
        if aa == bb:
            return ('Bob', None)         # the unique P-position shape
    else:
        g = q[1] - q[0] - 1
        h = q[-1] - q[-2] - 1

    if aa <= g + bb:                     # keep q[0]
        x = min(g, aa); y = aa - x
        L = q[0] + 1 + x
        R = n - y
        return ('Alice', (L, R))
    # keep q[-1]
    y = min(h, bb); x = bb - y
    L = x + 1
    R = q[-1] - 1 - y
    return ('Alice', (L, R))

# ------------------------------------------------------------------ checking
def move_ok(a, L, R):
    n = len(a)
    if not (1 <= L <= R <= n): return False, 'range'
    p = 1
    for v in a[L - 1:R]: p *= v
    if p != 1: return False, 'product'
    return True, tuple(a[:L - 1] + a[R:])

def check(a):
    a = list(a)
    w = win(tuple(a))
    who, mv = solve(a)
    if (who == 'Alice') != w:
        return 'WINNER %s brute=%s got=%s' % (a, w, who)
    if who == 'Alice':
        ok, rest = move_ok(a, *mv)
        if not ok: return 'INVALID %s %s (%s)' % (a, mv, rest)
        if win(rest): return 'LOSING %s %s -> %s' % (a, mv, list(rest))
    return None

SAMPLES = [([-1, -1, -1], 'Alice'), ([1, -1, -1], 'Alice'),
           ([-1], 'Bob'), ([1, -1, -1, -1, 1], 'Alice')]

if __name__ == '__main__':
    fail = 0
    print('--- samples from the statement ---')
    for a, exp in SAMPLES:
        who, mv = solve(list(a))
        note = ''
        if who == 'Alice':
            ok, rest = move_ok(list(a), *mv)
            note = ' move=%s valid=%s leaves=%s opp_wins=%s' % (
                mv, ok, list(rest) if ok else rest, win(rest) if ok else '?')
        good = (who == exp) and (who == 'Bob' or (ok and not win(rest)))
        fail += not good
        print(' ', a, 'expected', exp, '-> got', who, 'OK' if good else 'FAIL', note)

    print('--- exhaustive over every array, n <= 14 ---')
    bad = 0
    for n in range(1, 15):
        for mask in range(1 << n):
            a = [1 if (mask >> i) & 1 else -1 for i in range(n)]
            e = check(a)
            if e:
                bad += 1
                if bad < 10: print('  ', e)
    print('  mismatches:', bad); fail += bad

    print('--- random arrays, n <= 17, 400 trials ---')
    bad = 0
    random.seed(7)
    for _ in range(400):
        n = random.randint(1, 17)
        pneg = random.choice((0.2, 0.5, 0.85))
        a = [-1 if random.random() < pneg else 1 for _ in range(n)]
        e = check(a)
        if e:
            bad += 1
            if bad < 10: print('  ', e)
    print('  mismatches:', bad); fail += bad

    print('--- P-position shape check, n <= 14 ---')
    bad = 0
    for n in range(1, 15):
        for mask in range(1 << n):
            a = tuple(1 if (mask >> i) & 1 else -1 for i in range(n))
            neg = [i for i, x in enumerate(a) if x == -1]
            shape = (len(neg) == 1 and 2 * neg[0] + 1 == n)
            if shape != (not win(a)): bad += 1
    print('  mismatches:', bad); fail += bad

    print('ALL GOOD' if fail == 0 else 'FAILURES: %d' % fail)
