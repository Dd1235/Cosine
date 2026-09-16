"""reservoir: O(N) monotonic-stack computation of cap[i] = volume held when water stands exactly at
the brim of wall i, vs the O(N^2) definition (level of tank t = max(H_t..H_i), plus the water column
standing on top of each drowned wall).  Answer for a query K = #{ i : cap[i] < K } (strict: a
reservoir filled exactly to a wall's brim has not yet spilled over it -- pinned by sample query K=13)."""
import random

def widths(L):
    return [L[0]] + [L[i] - L[i-1] - 1 for i in range(1, len(L))]

def caps_stack(L, H):
    w = widths(L); vol = 0; st = []; caps = []
    for i in range(len(L)):
        target = H[i]; cur_w = w[i]
        vol += cur_w * target
        while st and st[-1][0] < target:
            lvl, wd = st.pop(); vol += wd * (target - lvl); cur_w += wd
        if st and st[-1][0] == target:
            cur_w += st.pop()[1]
        st.append((target, cur_w))
        caps.append(vol)
        st[-1] = (target, st[-1][1] + 1)   # the wall itself: solid up to H[i], can carry water above
    return caps

def caps_def(L, H):
    w = widths(L); out = []
    for i in range(len(L)):
        S = [0]*(i+1)
        run = 0
        for t in range(i, -1, -1):
            run = max(run, H[t]); S[t] = run
        v = sum(w[t]*S[t] for t in range(i+1))
        v += sum(max(0, S[t+1] - H[t]) for t in range(i))
        out.append(v)
    return out

def answer(caps, K):
    lo, hi = 0, len(caps)          # binary search: count of caps strictly below K
    while lo < hi:
        mid = (lo+hi)//2
        if caps[mid] < K: lo = mid+1
        else: hi = mid
    return lo

L, H = [1,3,5,8], [2,5,3,1]
c = caps_stack(L, H)
assert c == caps_def(L, H) == [2,13,16,18], c
assert [answer(c,k) for k in (3,13,17)] == [1,1,3], [answer(c,k) for k in (3,13,17)]

random.seed(13)
bad = 0
for t in range(2000):
    n = random.randint(1, 9)
    L = []; x = random.randint(1, 4)
    for i in range(n):
        L.append(x); x += random.randint(2, 5)
    H = [random.randint(1, 8) for _ in range(n)]
    a, b = caps_stack(L, H), caps_def(L, H)
    if a != b:
        bad += 1
        if bad < 4: print("MISMATCH", L, H, a, b)
    assert all(a[i] < a[i+1] for i in range(len(a)-1)), ("not increasing", L, H, a)
print("sample ok (caps [2,13,16,18] -> answers 1,1,3); mismatches =", bad)
