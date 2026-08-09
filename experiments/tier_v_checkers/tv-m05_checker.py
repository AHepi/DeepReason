#!/usr/bin/env python
"""Checker for tv-m05 (Tier V, math). Known answer: '835'.
Source: Hendrycks MATH (hendrycks/math, level 4-5 competition split) — counting_and_probability/test#4 (Level 4, Counting & Probability)
"""
import sys

ACCEPT = ['835']


def normalize(s):
    return str(s).strip().lstrip("+")


def check(answer):
    return normalize(answer) in {normalize(a) for a in ACCEPT}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: tv-m05_checker.py <answer>", file=sys.stderr)
        sys.exit(2)
    ok = check(sys.argv[1])
    print("PASS" if ok else "FAIL", sys.argv[1])
    sys.exit(0 if ok else 1)
