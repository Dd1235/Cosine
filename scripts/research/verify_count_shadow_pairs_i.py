"""count-shadow-pairs-i  (LeetCode Weekly 519)

Pair (i, j) counts iff  i < j, nums[i] < nums[j], and no k in (i, j) with nums[k] < nums[i].

Fast solution: single left-to-right monotonic stack.
  An index i is still a legal left endpoint at time j iff nums[i] <= min(nums[i+1..j-1]);
  such indices have non-decreasing values, so they are exactly a stack that is
  non-decreasing bottom->top.  On arriving at j we pop every entry with value > nums[j]
  (those can never be a left endpoint again), the survivors are the ones with value
  <= nums[j], and of those the ones with value == nums[j] fail the strict nums[i] < nums[j]
  test.  Entries are grouped by value with a multiplicity so ties are O(1).
  O(n) time, O(n) space.

Brute force: the definition, verbatim, O(n^3).
"""
import random


def fast(nums):
    stack = []          # (value, multiplicity), strictly increasing values bottom -> top
    size = 0            # sum of multiplicities
    ans = 0
    for v in nums:
        while stack and stack[-1][0] > v:
            size -= stack.pop()[1]
        eq = stack[-1][1] if stack and stack[-1][0] == v else 0
        ans += size - eq                 # entries with value strictly less than v
        if stack and stack[-1][0] == v:
            stack[-1] = (v, stack[-1][1] + 1)
        else:
            stack.append((v, 1))
        size += 1
    return ans


def brute(nums):
    n = len(nums)
    ans = 0
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] >= nums[j]:
                continue
            if any(nums[k] < nums[i] for k in range(i + 1, j)):
                continue
            ans += 1
    return ans


EXAMPLES = [([3, 1, 4, 1, 5], 3), ([6, 7, 6, 6, 7], 4), ([1, 2, 3, 4], 6)]

if __name__ == "__main__":
    for nums, want in EXAMPLES:
        got = fast(nums)
        print("example", nums, "expected", want, "got", got, "OK" if got == want else "MISMATCH")
        assert got == want, (nums, want, got)
        assert brute(nums) == want

    random.seed(519)
    trials = 0
    for _ in range(5000):
        n = random.randint(3, 12)
        hi = random.choice([2, 3, 5, 10, 10 ** 9])
        nums = [random.randint(1, hi) for _ in range(n)]
        f, b = fast(nums), brute(nums)
        assert f == b, (nums, f, b)
        trials += 1
    # a few larger ones
    for _ in range(60):
        n = random.randint(50, 200)
        hi = random.choice([3, 8, 50, 10 ** 9])
        nums = [random.randint(1, hi) for _ in range(n)]
        assert fast(nums) == brute(nums), nums
        trials += 1
    # structured shapes
    for nums in ([1] * 50, list(range(1, 51)), list(range(50, 0, -1)),
                 [1, 2] * 25, [5] * 20 + [1] * 20 + [9] * 20):
        assert fast(nums) == brute(nums), nums
        trials += 1
    print("random + structured trials passed:", trials)
