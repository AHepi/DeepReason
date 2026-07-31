"""Independent brute-force oracle for coin-system canonicity.

Used to judge both the native answer and the harness run against fact,
rather than against either model's own account of itself. Exact integer
arithmetic; no sampling.

Run from this directory:  python3 oracle.py
"""

from __future__ import annotations

import itertools


def greedy_count(coins: tuple[int, ...], w: int) -> int:
    used = 0
    for c in coins:                       # coins are strictly decreasing
        if c <= w:
            used += w // c
            w -= c * (w // c)
        if w == 0:
            break
    return used


def optimal_counts(coins: tuple[int, ...], limit: int) -> list[int]:
    best = [0] + [None] * limit
    for w in range(1, limit + 1):
        candidates = [best[w - c] for c in coins if c <= w and best[w - c] is not None]
        best[w] = 1 + min(candidates) if candidates else None
    return best


def smallest_counterexample(coins: tuple[int, ...], limit: int) -> int | None:
    """Smallest w <= limit with greedy(w) > optimal(w), or None."""
    opt = optimal_counts(coins, limit)
    for w in range(1, limit + 1):
        if opt[w] is not None and greedy_count(coins, w) > opt[w]:
            return w
    return None


def systems(max_value: int, max_coins: int):
    """Every strictly decreasing system ending in 1 with values <= max_value."""
    for size in range(2, max_coins + 1):
        for middle in itertools.combinations(range(2, max_value + 1), size - 1):
            yield tuple(sorted(middle, reverse=True)) + (1,)


def main() -> None:
    # The search limit is deliberately far above any bound under test, so
    # the oracle's verdict does not depend on the bound being judged.
    def limit_for(coins):
        return 4 * (coins[0] + coins[1]) + 8

    print("== 1. the textbook system, against the native answer's bound ==")
    coins = (4, 3, 1)
    w = smallest_counterexample(coins, limit_for(coins))
    print(f"    system {coins}: smallest counterexample = {w}")
    print(f"      greedy({w}) = {greedy_count(coins, w)},"
          f" optimal({w}) = {optimal_counts(coins, w)[w]}")
    print(f"      native bound c_1 + c_3 = {coins[0] + coins[2]}"
          f"  -> {'REFUTED' if w > coins[0] + coins[2] else 'survives'}")
    print(f"      Kozen-Zaks c_1 + c_2  = {coins[0] + coins[1]}"
          f"  -> {'refuted' if w > coins[0] + coins[1] else 'SURVIVES'}")

    print("== 2. exhaustive sweep of small systems ==")
    total = noncanonical = 0
    beats_c1c3 = []
    beats_c1c2 = []
    worst_ratio = (0.0, None, None)
    for coins in systems(max_value=24, max_coins=5):
        total += 1
        w = smallest_counterexample(coins, limit_for(coins))
        if w is None:
            continue
        noncanonical += 1
        if len(coins) >= 3 and w > coins[0] + coins[2]:
            beats_c1c3.append((coins, w, coins[0] + coins[2]))
        if w > coins[0] + coins[1]:
            beats_c1c2.append((coins, w, coins[0] + coins[1]))
        ratio = w / (coins[0] + coins[1])
        if ratio > worst_ratio[0]:
            worst_ratio = (ratio, coins, w)

    print(f"    systems enumerated              : {total}")
    print(f"    non-canonical among them        : {noncanonical}")
    print(f"    smallest counterexample > c1+c3 : {len(beats_c1c3)}"
          f"   <- each one refutes the native bound")
    print(f"    smallest counterexample > c1+c2 : {len(beats_c1c2)}"
          f"   <- each one would refute Kozen-Zaks")
    print(f"    largest observed w/(c1+c2)      : {worst_ratio[0]:.4f}"
          f"  at {worst_ratio[1]}, w={worst_ratio[2]}")
    print("    first five systems refuting the native bound:")
    for coins, w, bound in beats_c1c3[:5]:
        print(f"      {coins}: smallest counterexample {w} > c1+c3 = {bound}")


if __name__ == "__main__":
    main()
