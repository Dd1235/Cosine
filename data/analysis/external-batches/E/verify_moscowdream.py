"""Moscow Dream (kattis-moscowdream) -- brute force vs closed-form check.

Claim: answer is YES iff a>=1 and b>=1 and c>=1 and 3 <= n <= a+b+c.
Brute force: enumerate every (x,y,z) with 1<=x<=a, 1<=y<=b, 1<=z<=c, x+y+z==n.
Exhaustive over the whole input space 0<=a,b,c<=10, 1<=n<=20.
"""

def brute(a, b, c, n):
    for x in range(1, a + 1):
        for y in range(1, b + 1):
            for z in range(1, c + 1):
                if x + y + z == n:
                    return True
    return False


def formula(a, b, c, n):
    return a >= 1 and b >= 1 and c >= 1 and 3 <= n <= a + b + c


def main():
    bad = 0
    for a in range(11):
        for b in range(11):
            for c in range(11):
                for n in range(1, 21):
                    if brute(a, b, c, n) != formula(a, b, c, n):
                        bad += 1
                        if bad < 10:
                            print("MISMATCH", a, b, c, n, brute(a, b, c, n), formula(a, b, c, n))
    print("mismatches:", bad)
    # samples
    assert formula(0, 3, 3, 5) is False
    assert formula(4, 10, 6, 13) is True
    print("samples OK")


main()
