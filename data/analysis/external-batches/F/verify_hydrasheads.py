"""Hydra's Heads: closed form vs BFS over the (heads, tails) state graph.

Effective moves (move 1, 'cut one head', regrows a head and is a no-op):
  T>=1: (H,T) -> (H, T+1)
  H>=2: (H,T) -> (H-2, T)
  T>=2: (H,T) -> (H+1, T-2)
Goal (0,0).  With a = #(T+1) moves, b = #(H-2) moves, c = #(H+1,T-2) moves:
  a = 2c - T, 2b = H + c, total = 3c - T + (H+c)//2, minimised at the smallest
  c >= ceil(T/2) with c == H (mod 2).  Any such plan is orderable: do all a
  first, then all c, then all b.
"""
from collections import deque

LIM = 400


def formula(H, T):
    c = (T + 1) // 2
    if (c - H) % 2:
        c += 1
    return 3 * c - T + (H + c) // 2


def bfs_table():
    dist = [[-1] * (LIM + 1) for _ in range(LIM + 1)]
    dist[0][0] = 0
    q = deque([(0, 0)])
    while q:
        h, t = q.popleft()
        d = dist[h][t]
        preds = []
        if t >= 2:
            preds.append((h, t - 1))          # predecessor used move 2
        if h + 2 <= LIM:
            preds.append((h + 2, t))          # predecessor used move 3
        if h >= 1 and t + 2 <= LIM:
            preds.append((h - 1, t + 2))      # predecessor used move 4
        for (ph, pt) in preds:
            if dist[ph][pt] == -1:
                dist[ph][pt] = d + 1
                q.append((ph, pt))
    return dist


def main():
    assert formula(3, 3) == 9, formula(3, 3)
    assert formula(1, 1) == 3, formula(1, 1)
    print("samples ok")
    dist = bfs_table()
    bad = 0
    for H in range(1, 101):
        for T in range(1, 101):
            if dist[H][T] != formula(H, T):
                bad += 1
                if bad < 5:
                    print("MISMATCH", H, T, dist[H][T], formula(H, T))
    assert bad == 0, bad
    print("all 100x100 (H,T) states match BFS; no state is unreachable")


main()
