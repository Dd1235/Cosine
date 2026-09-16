"""ICPC Awards: given a scoreboard of N (12..200) teams in rank order, each line
"university team", print the 12 prize winners -- scan top to bottom and keep a team
only if no better-ranked team from the same university has already been kept, until
12 are kept.  Output in input order.  O(N) with a hash set of seen universities.

Check: the sample, plus an independent O(N^2) re-implementation on random boards.
"""
import random, string

def solve(rows):
    seen=set(); out=[]
    for u,t in rows:
        if u in seen: continue
        seen.add(u); out.append((u,t))
        if len(out)==12: break
    return out

def brute(rows):
    out=[]
    for i,(u,t) in enumerate(rows):
        if len(out)==12: break
        if any(rows[j][0]==u for j in range(i)): continue
        out.append((u,t))
    return out

SAMPLE = """Seoul ACGTeam
VNU LINUX
SJTU Mjolnir
VNU WINDOWS
NTU PECaveros
HUST BKJuniors
HCMUS HCMUSSerendipity
VNU UBUNTU
SJTU Metis
HUST BKDeepMind
HUST BKTornado
HCMUS HCMUSLattis
NUS Tourism
VNU DOS
HCMUS HCMUSTheCows
VNU ANDROID
HCMUS HCMUSPacman
HCMUS HCMUSGeomecry
UIndonesia DioramaBintang
VNU SOLARIS
UIndonesia UIChan
FPT ACceptable
HUST BKIT
PTIT Miners
PSA PSA
DaNangUT BDTTNeverGiveUp
VNU UNIXBSD
CanTho CTUA2LTT
Soongsil Team10deung
Soongsil BezzerBeater"""

EXPECT = """Seoul ACGTeam
VNU LINUX
SJTU Mjolnir
NTU PECaveros
HUST BKJuniors
HCMUS HCMUSSerendipity
NUS Tourism
UIndonesia DioramaBintang
FPT ACceptable
PTIT Miners
PSA PSA
DaNangUT BDTTNeverGiveUp"""

def main():
    rows=[tuple(l.split()) for l in SAMPLE.splitlines()]
    exp=[tuple(l.split()) for l in EXPECT.splitlines()]
    got=solve(rows)
    assert got==exp, got
    print("sample OK")
    random.seed(2)
    for _ in range(500):
        unis=[random.choice(string.ascii_uppercase[:20]) for _ in range(random.randint(30,60))]
        while len(set(unis))<12:
            unis.append(random.choice(string.ascii_uppercase[:20]))
        rows=[(u,"T%d"%i) for i,u in enumerate(unis)]
        assert solve(rows)==brute(rows)
    print("random boards OK")
    print("icpcawards: OK")

main()
