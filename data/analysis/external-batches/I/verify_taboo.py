"""Brute force check for kattis-taboo.

Solution under test: build the Aho-Corasick automaton of the taboo strings, mark
a state bad when it or any state on its suffix-link chain ends a taboo string,
and keep only good states.  Legal clues are exactly the walks from the root that
never enter a bad state, so the answer is the longest such walk: if any good
state reachable from the root lies on a cycle of good states the clue is
unbounded (-1), otherwise a DP over the acyclic automaton gives the length and a
greedy walk taking '0' whenever it keeps the maximum gives the lexicographically
smallest longest clue.  O(total length) states and transitions.
"""
import random
from itertools import product


def solve(words):
    nxt = [[-1, -1]]
    term = [False]
    for w in words:
        cur = 0
        for ch in w:
            c = ord(ch) - 48
            if nxt[cur][c] == -1:
                nxt.append([-1, -1])
                term.append(False)
                nxt[cur][c] = len(nxt) - 1
            cur = nxt[cur][c]
        term[cur] = True
    n = len(nxt)
    link = [0] * n
    order = []
    from collections import deque
    q = deque()
    for c in range(2):
        v = nxt[0][c]
        if v == -1:
            nxt[0][c] = 0
        else:
            link[v] = 0
            q.append(v)
    while q:
        u = q.popleft()
        order.append(u)
        term[u] = term[u] or term[link[u]]
        for c in range(2):
            v = nxt[u][c]
            if v == -1:
                nxt[u][c] = nxt[link[u]][c]
            else:
                link[v] = nxt[link[u]][c]
                q.append(v)
    # longest walk over good states
    if term[0]:
        return ""
    NOTDONE, INPROG, DONE = 0, 1, 2
    state = [NOTDONE] * n
    best = [0] * n
    choice = [-1] * n
    stack = [(0, 0)]
    while stack:
        u, phase = stack.pop()
        if phase == 0:
            if state[u] == DONE:
                continue
            if state[u] == INPROG:
                return None  # cycle -> unbounded
            state[u] = INPROG
            stack.append((u, 1))
            for c in range(2):
                v = nxt[u][c]
                if not term[v] and state[v] != DONE:
                    if state[v] == INPROG:
                        return None
                    stack.append((v, 0))
        else:
            b, ch = 0, -1
            for c in range(2):
                v = nxt[u][c]
                if not term[v]:
                    if state[v] != DONE:
                        return None
                    if 1 + best[v] > b:
                        b, ch = 1 + best[v], c
            best[u], choice[u] = b, ch
            state[u] = DONE
    out = []
    u = 0
    while choice[u] != -1:
        # prefer '0' when it keeps the optimum
        c = 0 if (not term[nxt[u][0]] and 1 + best[nxt[u][0]] == best[u]) else 1
        out.append(str(c))
        u = nxt[u][c]
    return "".join(out)


def brute(words, cap):
    best = None
    for length in range(0, cap + 1):
        found = None
        for tup in product("01", repeat=length):
            s = "".join(tup)
            if all(w not in s for w in words):
                found = s
                break
        if found is None:
            return best
        best = found
    return None  # still going at the cap -> unbounded


def main():
    assert solve(["00", "01", "10", "110", "111"]) == "11", solve(["00", "01", "10", "110", "111"])
    assert solve(["00", "01", "10"]) is None
    print("samples OK")
    rng = random.Random(3)
    bad = 0
    for _ in range(300):
        n = rng.randint(1, 5)
        words = list({"".join(rng.choice("01") for _ in range(rng.randint(1, 4)))
                      for _ in range(n)})
        total = sum(len(w) for w in words)
        cap = total + 3
        mine = solve(words)
        ref = brute(words, cap)
        if mine is None:
            ok = ref is None
        else:
            ok = ref is not None and len(mine) == len(ref) and mine == ref
        if not ok:
            bad += 1
            print("MISMATCH", words, "mine=", mine, "brute=", ref)
            if bad > 5:
                return
    print("random trials %s" % ("OK" if bad == 0 else "%d FAILURES" % bad))


if __name__ == "__main__":
    main()
