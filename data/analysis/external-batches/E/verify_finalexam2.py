"""Final Exam (kattis-finalexam2) -- literal simulation vs one-pass formula.

Hanh writes the answer to question i+1 on line i (1-indexed), leaving line n blank.
Line i is graded against the key for question i, so he scores a point exactly when
key[i] == key[i+1].  Claim: answer = #{i in [1, n-1] : key[i] == key[i+1]}.

Brute force literally builds the sheet and grades it line by line.
"""
import random


def brute(key):
    n = len(key)
    sheet = [None] * n              # sheet[i] = what Hanh wrote on line i (0-indexed)
    for i in range(n - 1):          # line i gets the answer for question i+1
        sheet[i] = key[i + 1]
    # line n-1 left empty
    score = 0
    for i in range(n):
        if sheet[i] is not None and sheet[i] == key[i]:
            score += 1
    return score


def formula(key):
    return sum(1 for i in range(len(key) - 1) if key[i] == key[i + 1])


def main():
    assert brute("AAAA") == 3 and formula("AAAA") == 3
    assert brute("ADBBCA") == 1 and formula("ADBBCA") == 1
    print("samples OK")
    random.seed(1)
    bad = 0
    for _ in range(20000):
        n = random.randint(1, 12)
        alpha = random.choice(["AB", "ABCD", "A"])     # skew toward collisions
        key = "".join(random.choice(alpha) for _ in range(n))
        if brute(key) != formula(key):
            bad += 1
            print("MISMATCH", key, brute(key), formula(key))
    # exhaustive over all keys up to length 8 on a 2-letter alphabet
    from itertools import product
    for n in range(1, 9):
        for t in product("AB", repeat=n):
            key = "".join(t)
            if brute(key) != formula(key):
                bad += 1
    print("mismatches:", bad)


main()
