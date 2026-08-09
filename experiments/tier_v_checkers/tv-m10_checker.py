#!/usr/bin/env python
"""Checker for tv-m10 (Tier V, math). Known answer: '144'.
Source: Hendrycks MATH (hendrycks/math, level 4-5 competition split) — precalculus/test#59 (Level 4, Precalculus)
"""
import sys

ACCEPT = ['144']


def normalize(s):
    return str(s).strip().lstrip("+")


def check(answer):
    return normalize(answer) in {normalize(a) for a in ACCEPT}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: tv-m10_checker.py <answer>", file=sys.stderr)
        sys.exit(2)
    ok = check(sys.argv[1])
    print("PASS" if ok else "FAIL", sys.argv[1])
    sys.exit(0 if ok else 1)
