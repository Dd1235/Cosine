"""count-shadow-pairs-ii  (LeetCode Weekly 519)

Pair (i, j) counts iff  i < j, nums[i] < nums[j], and no k in (i, j) with
nums[i] < nums[k] < nums[j].   (I forbade nums[k] < nums[i]; II forbids a value
strictly BETWEEN the two endpoints, so the blocked set depends on both endpoints
and the stack of part I no longer applies.)

The answer can be quadratic ( [1]*n/2 + [2]*n/2 gives n^2/4 pairs ), so the pairs
must be counted, never enumerated.

Fast solution: divide and conquer over the index range, O(n log^2 n) / O(n) space.
For a split point mid, a crossing pair has i <= mid < j and the forbidden window
(i, j) splits into (i, mid] and [mid+1, j):
    left  part:  every value > nums[i] there must be >= nums[j]
                 <=>  nums[j] <= A_i,  A_i = min{ v_k : k in (i,mid], v_k > nums[i] }
    right part:  every value < nums[j] there must be <= nums[i]
                 <=>  D_j <= nums[i],  D_j = max{ v_k : k in [mid+1,j), v_k < nums[j] }
A_i depends only on i and D_j only on j, so the crossing pairs are exactly
    #{ (i,j) : D_j <= nums[i] < nums[j] <= A_i }.
A_i / D_j are successor / predecessor queries over a growing set (Fenwick tree with
a binary descent), and the final count is a 2-D dominance count: sweep j by
decreasing nums[j], insert every left i with A_i >= nums[j], and ask the Fenwick
tree how many inserted nums[i] lie in [D_j, nums[j] - 1].

Brute force: the definition, verbatim, O(n^3).
"""
import random
import sys


class Fenwick:
    """Counts over ranks 0..n-1, with k-th / successor / predecessor by binary descent."""

    __slots__ = ("n", "t", "tot", "pw")

    def __init__(self, n):
        self.n = n
        self.t = [0] * (n + 1)
        self.tot = 0
        p = 1
        while p * 2 <= n:
            p *= 2
        self.pw = p

    def add(self, i, v=1):
        self.tot += v
        i += 1
        while i <= self.n:
            self.t[i] += v
            i += i & -i

    def prefix(self, i):          # how many stored ranks are <= i (i may be < 0)
        i += 1
        s = 0
        while i > 0:
            s += self.t[i]
            i -= i & -i
        return s

    def kth(self, k):             # 0-indexed rank of the k-th smallest (k >= 1)
        pos = 0
        rem = k
        pw = self.pw
        while pw:
            nxt = pos + pw
            if nxt <= self.n and self.t[nxt] < rem:
                pos = nxt
                rem -= self.t[pos]
            pw >>= 1
        return pos

    def successor(self, r, sentinel):   # smallest stored rank strictly > r
        c = self.prefix(r)
        return self.kth(c + 1) if c < self.tot else sentinel

    def predecessor(self, r):           # largest stored rank strictly < r, else -1
        c = self.prefix(r - 1)
        return self.kth(c) if c > 0 else -1


def fast(nums):
    n = len(nums)
    order = sorted(set(nums))
    rk = {v: i for i, v in enumerate(order)}
    a = [rk[v] for v in nums]

    total = 0
    stack = [(0, n - 1, False)]
    while stack:
        lo, hi, done = stack.pop()
        if lo >= hi:
            continue
        mid = (lo + hi) // 2
        if not done:
            stack.append((lo, hi, True))
            stack.append((lo, mid, False))
            stack.append((mid + 1, hi, False))
            continue

        # local compression keeps every Fenwick tree segment-sized
        seg = a[lo:hi + 1]
        loc = sorted(set(seg))
        idx = {v: i for i, v in enumerate(loc)}
        k = len(loc)
        b = [idx[x] for x in seg]
        ml = mid - lo                      # local index of mid

        bit = Fenwick(k)
        left = []
        for t in range(ml, -1, -1):
            r = b[t]
            left.append((bit.successor(r, k), r))   # (A_i, nums[i])
            bit.add(r)

        bit = Fenwick(k)
        right = []
        for t in range(ml + 1, hi - lo + 1):
            r = b[t]
            right.append((r, bit.predecessor(r)))   # (nums[j], D_j)
            bit.add(r)

        left.sort(key=lambda e: -e[0])
        right.sort(key=lambda e: -e[0])
        bit = Fenwick(k)
        p = 0
        nl = len(left)
        for aj, dj in right:
            while p < nl and left[p][0] >= aj:
                bit.add(left[p][1])
                p += 1
            total += bit.prefix(aj - 1) - bit.prefix(dj - 1)
    return total


def brute(nums):
    n = len(nums)
    ans = 0
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] >= nums[j]:
                continue
            if any(nums[i] < nums[k] < nums[j] for k in range(i + 1, j)):
                continue
            ans += 1
    return ans


EXAMPLES = [([3, 1, 4, 2, 5], 5), ([6, 7, 8, 9], 3)]

if __name__ == "__main__":
    for nums, want in EXAMPLES:
        got = fast(nums)
        print("example", nums, "expected", want, "got", got, "OK" if got == want else "MISMATCH")
        assert got == want, (nums, want, got)
        assert brute(nums) == want

    random.seed(5192)
    trials = 0
    for _ in range(5000):
        n = random.randint(3, 12)
        hi = random.choice([2, 3, 4, 7, 12, 10 ** 9])
        nums = [random.randint(1, hi) for _ in range(n)]
        f, b = fast(nums), brute(nums)
        assert f == b, (nums, f, b)
        trials += 1
    for _ in range(400):                       # sizes that cross several D&C levels
        n = random.randint(13, 40)
        hi = random.choice([2, 5, 15, 40, 10 ** 9])
        nums = [random.randint(1, hi) for _ in range(n)]
        f, b = fast(nums), brute(nums)
        assert f == b, (nums, f, b)
        trials += 1
    for _ in range(40):
        n = random.randint(120, 260)
        hi = random.choice([3, 10, 100, 10 ** 9])
        nums = [random.randint(1, hi) for _ in range(n)]
        f, b = fast(nums), brute(nums)
        assert f == b, (nums, f, b)
        trials += 1
    for nums in ([1] * 40, list(range(1, 61)), list(range(60, 0, -1)),
                 [1] * 30 + [2] * 30, [1, 2] * 30, [3] * 20 + [1] * 20 + [2] * 20,
                 list(range(1, 31)) + list(range(30, 0, -1))):
        f, b = fast(nums), brute(nums)
        assert f == b, (nums[:8], f, b)
        trials += 1
    print("random + structured trials passed:", trials)

    if "--time" in sys.argv:
        import time
        for nums in ([random.randint(1, 10 ** 9) for _ in range(50000)],
                     [random.randint(1, 2) for _ in range(50000)],
                     list(range(50000))):
            t0 = time.time()
            r = fast(nums)
            print("n=50000 answer", r, "in %.2fs" % (time.time() - t0))
