"""Conquest Campaign: multi-source BFS answer vs literal day-by-day simulation."""
import random
from collections import deque


def solve_bfs(R, C, sources):
    INF = -1
    dist = [[INF] * C for _ in range(R)]
    q = deque()
    for (x, y) in sources:
        if dist[x][y] == INF:
            dist[x][y] = 0
            q.append((x, y))
    best = 0
    while q:
        x, y = q.popleft()
        best = max(best, dist[x][y])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < R and 0 <= ny < C and dist[nx][ny] == INF:
                dist[nx][ny] = dist[x][y] + 1
                q.append((nx, ny))
    return best + 1


def solve_sim(R, C, sources):
    occ = [[False] * C for _ in range(R)]
    for (x, y) in sources:
        occ[x][y] = True
    days = 1
    while not all(all(row) for row in occ):
        new = []
        for i in range(R):
            for j in range(C):
                if occ[i][j]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < R and 0 <= nj < C and occ[ni][nj]:
                        new.append((i, j))
                        break
        for (i, j) in new:
            occ[i][j] = True
        days += 1
    return days


def samples():
    assert solve_bfs(3, 4, [(1, 1), (1, 1), (2, 3)]) == 3
    assert solve_bfs(2, 3, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]) == 1
    print("samples ok")


def main():
    samples()
    random.seed(11)
    for _ in range(4000):
        R = random.randint(1, 8)
        C = random.randint(1, 8)
        n = random.randint(1, 4)
        src = [(random.randrange(R), random.randrange(C)) for _ in range(n)]
        a, b = solve_bfs(R, C, src), solve_sim(R, C, src)
        assert a == b, (R, C, src, a, b)
    print("4000 random cases ok")


main()
