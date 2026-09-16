"""Lazy Learner: offline sweep (per left endpoint) vs naive per-query search.

Key fact: for a fixed left endpoint l, word T is a subsequence of S[l..r] iff
r >= f(l, T), where f(l, T) is the end position of the greedy leftmost match of
T starting at l (greedy matching is optimal for subsequence containment).  So
per l the query 'k-th lexicographically smallest word with f(l,T) <= r' is a
k-th-one query over a Fenwick tree indexed by lexicographic rank, answered by
sweeping r upward and inserting words in increasing f(l,.) order.
"""
import random

LIM = 10


class BIT:
    def __init__(self, n):
        self.n = n
        self.t = [0] * (n + 1)
        self.LOG = max(1, n.bit_length())

    def add(self, i, v):
        i += 1
        while i <= self.n:
            self.t[i] += v
            i += i & -i

    def kth(self, k):
        """smallest index whose prefix count >= k, or -1"""
        pos, rem = 0, k
        pw = 1 << self.LOG
        while pw:
            if pos + pw <= self.n and self.t[pos + pw] < rem:
                pos += pw
                rem -= self.t[pos]
            pw >>= 1
        return pos if pos < self.n else -1


def fast(S, words, queries):
    n, m = len(words), len(S)
    order = sorted(range(n), key=lambda i: words[i])
    rank = [0] * n
    for r, i in enumerate(order):
        rank[i] = r
    # nxt[p][c] = smallest index >= p with S[index]==c, else m
    nxt = [[m] * 26 for _ in range(m + 1)]
    for p in range(m - 1, -1, -1):
        row = nxt[p + 1][:]
        row[ord(S[p]) - 97] = p
        nxt[p] = row

    by_l = {}
    for qi, (l, r, k) in enumerate(queries):
        by_l.setdefault(l, []).append((r, k, qi))
    ans = [None] * len(queries)

    for l, qs in by_l.items():
        # f(l, word) as a 0-based end index (exclusive), m+1 means impossible
        buckets = [[] for _ in range(m + 2)]
        for i, w in enumerate(words):
            p = l - 1
            ok = True
            for ch in w:
                p = nxt[p][ord(ch) - 97]
                if p == m:
                    ok = False
                    break
                p += 1
            buckets[p if ok else m + 1].append(i)
        bit = BIT(n)
        qs.sort()
        cur = 0
        for (r, k, qi) in qs:
            while cur <= r:            # r is 1-based; p is 1-based end too
                for i in buckets[cur]:
                    bit.add(rank[i], 1)
                cur += 1
            idx = bit.kth(k)
            ans[qi] = "NO SUCH WORD" if idx < 0 else words[order[idx]][:LIM]
    return ans


def naive(S, words, queries):
    out = []
    for (l, r, k) in queries:
        sub = S[l - 1:r]
        got = []
        for w in words:
            it = iter(sub)
            if all(c in it for c in w):
                got.append(w)
        got.sort()
        out.append(got[k - 1][:LIM] if k <= len(got) else "NO SUCH WORD")
    return out


def main():
    S = "abcd"
    words = ["a", "ac", "bd"]
    qs = [(1, 3, 1), (1, 3, 2), (1, 3, 3), (2, 4, 1), (2, 4, 2)]
    exp = ["a", "ac", "NO SUCH WORD", "bd", "NO SUCH WORD"]
    assert fast(S, words, qs) == exp, fast(S, words, qs)
    print("sample ok")

    random.seed(7)
    for t in range(600):
        alpha = random.choice(["ab", "abc", "abcd"])
        S = "".join(random.choice(alpha) for _ in range(random.randint(1, 12)))
        nw = random.randint(1, 8)
        words = ["".join(random.choice(alpha)
                         for _ in range(random.randint(1, 4))) for _ in range(nw)]
        qs = []
        for _ in range(12):
            l = random.randint(1, len(S))
            r = random.randint(l, len(S))
            qs.append((l, r, random.randint(1, nw)))
        a, b = fast(S, words, qs), naive(S, words, qs)
        assert a == b, (S, words, qs, a, b)
    print("600 random cases ok (duplicate words included)")


main()
