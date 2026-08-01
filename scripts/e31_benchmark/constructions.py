"""Randomized program-checkable construction problems for E3.1 class 2.

Each problem is a parameterized combinatorial target ("build an object of
size N satisfying properties P1..Pk") with:

- a trusted checker function (single source of truth; the sealed standalone
  checker script embeds the exact same function source via ``inspect``), run
  under the code-workload :class:`CheckSpec` conventions
  (src/deepreason/workloads/code.py);
- a brute-force baseline executed at build time that certifies solvability
  (at least one witness exists) and measures the search-space size.

Parameters are randomized deterministically from the seed at benchmark build
time; unsolvable parameterizations are rejected and regenerated with an
attempt counter (recorded — never silently patched).

The problem statement and parameters are problem-facing (a solver must know
what to build).  The checker bytes and the answer key (witness + brute-force
census) are sealed per harness-spec-v1.3 §10.5.
"""

from __future__ import annotations

import inspect
import json
import math
import random
from dataclasses import dataclass
from itertools import combinations, permutations
from typing import Any

from deepreason.workloads.code import CheckSpec

GENERATOR_VERSION = "e31-constructions-v1"

FAMILIES = ("sidon_residue", "forbidden_words", "displaced_permutation")


# --- trusted checker functions (single source of truth) ----------------------
# Each takes (params, candidate) and returns (ok: bool, reason: str).  The
# sealed checker script embeds the function source verbatim, so what the
# tests exercise in-process is byte-identical to what runs at Reveal.

def check_sidon_residue(params, candidate):
    n, m = params["n"], params["m"]
    q, r = params["q"], params["r"]
    if not isinstance(candidate, list) or len(candidate) != n:
        return False, f"candidate must be a list of exactly {n} integers"
    if any(not isinstance(item, int) or isinstance(item, bool) for item in candidate):
        return False, "candidate entries must be integers"
    if len(set(candidate)) != n:
        return False, "entries must be distinct"
    if any(item < 1 or item > m for item in candidate):
        return False, f"entries must lie in [1, {m}]"
    sums = [a + b for i, a in enumerate(candidate) for b in candidate[i + 1:]]
    if len(sums) != len(set(sums)):
        return False, "pairwise sums must be distinct (Sidon property)"
    if sum(candidate) % q != r:
        return False, f"sum must be congruent to {r} mod {q}"
    return True, "all properties satisfied"


def check_forbidden_words(params, candidate):
    n, k = params["n"], params["k"]
    forbidden = params["forbidden"]
    if not isinstance(candidate, str) or len(candidate) != n:
        return False, f"candidate must be a string of length {n}"
    if any(ch not in "01" for ch in candidate):
        return False, "candidate must be a binary string"
    if candidate.count("1") != k:
        return False, f"candidate must contain exactly {k} ones"
    for word in forbidden:
        if word in candidate:
            return False, f"candidate contains forbidden substring {word}"
    return True, "all properties satisfied"


def check_displaced_permutation(params, candidate):
    n = params["n"]
    banned = set(params["banned_displacements"])
    q, r = params["q"], params["r"]
    if not isinstance(candidate, list) or sorted(candidate) != list(range(n)):
        return False, f"candidate must be a permutation of 0..{n - 1}"
    displacements = [abs(value - index) for index, value in enumerate(candidate)]
    if any(d == 0 for d in displacements):
        return False, "permutation must be fixed-point-free"
    hit = sorted(set(displacements) & banned)
    if hit:
        return False, f"banned displacement(s) used: {hit}"
    if sum(displacements) % q != r:
        return False, f"total displacement must be congruent to {r} mod {q}"
    return True, "all properties satisfied"


_CHECKERS = {
    "sidon_residue": check_sidon_residue,
    "forbidden_words": check_forbidden_words,
    "displaced_permutation": check_displaced_permutation,
}

_CHECKER_MAIN = '''

def main():
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "candidate.json"
    with open(path, encoding="utf-8") as handle:
        candidate = json.load(handle)
    ok, reason = {fn_name}(PARAMS, candidate)
    print(("PASS: " if ok else "FAIL: ") + reason)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def render_checker(family: str, params: dict[str, Any], problem_id: str) -> str:
    """Standalone trusted checker script (sealed until Reveal)."""

    fn = _CHECKERS[family]
    source = inspect.getsource(fn)
    header = (
        "#!/usr/bin/env python3\n"
        f'"""E3.1 trusted checker for {problem_id} (family {family}).\n\n'
        "Sealed holdout artifact (harness-spec-v1.3 SS10.5): withheld from any\n"
        'run loop, revealed only post-hoc.  Exit 0 iff the candidate passes."""\n'
        "import json\n\n"
        f"PARAMS = json.loads({json.dumps(json.dumps(params, sort_keys=True))})\n\n"
    )
    return header + source + _CHECKER_MAIN.format(fn_name=fn.__name__)


# --- brute-force solvability baselines ---------------------------------------

_ENUM_CAP = 2_000_000  # hard step ceiling for every build-time enumeration


def _brute_sidon(params) -> dict[str, Any]:
    n, m, q, r = params["n"], params["m"], params["q"], params["r"]
    steps = 0
    solutions = 0
    witness: list[int] | None = None
    cap_hit = False

    def extend(prefix: list[int], sums: set[int], start: int) -> None:
        nonlocal steps, solutions, witness, cap_hit
        if cap_hit:
            return
        if len(prefix) == n:
            steps += 1
            if steps >= _ENUM_CAP:
                cap_hit = True
            if sum(prefix) % q == r:
                solutions += 1
                if witness is None:
                    witness = list(prefix)
            return
        for value in range(start, m + 1):
            steps += 1
            if steps >= _ENUM_CAP:
                cap_hit = True
                return
            new_sums = {value + item for item in prefix}
            if len(new_sums) != len(prefix) or new_sums & sums:
                continue
            prefix.append(value)
            extend(prefix, sums | new_sums, value + 1)
            prefix.pop()

    extend([], set(), 1)
    return {
        "search_space_size": math.comb(m, n),
        "search_space_note": f"C({m},{n}) increasing n-subsets of [1,{m}]",
        "candidates_enumerated": math.comb(m, n),
        "enumeration_steps": steps,
        "enumeration_cap": _ENUM_CAP,
        "cap_hit": cap_hit,
        "solutions_found": solutions,
        "witness": witness,
    }


def _brute_forbidden_words(params) -> dict[str, Any]:
    n, k = params["n"], params["k"]
    forbidden = params["forbidden"]
    steps = 0
    solutions = 0
    witness: str | None = None
    cap_hit = False
    for ones in combinations(range(n), k):
        steps += 1
        if steps >= _ENUM_CAP:
            cap_hit = True
            break
        word = "".join("1" if index in ones else "0" for index in range(n))
        if any(bad in word for bad in forbidden):
            continue
        solutions += 1
        if witness is None:
            witness = word
    return {
        "search_space_size": 2 ** n,
        "search_space_note": f"2^{n} binary strings (C({n},{k})="
        f"{math.comb(n, k)} with the ones-count constraint)",
        "candidates_enumerated": math.comb(n, k),
        "enumeration_steps": steps,
        "enumeration_cap": _ENUM_CAP,
        "cap_hit": cap_hit,
        "solutions_found": solutions,
        "witness": witness,
    }


def _brute_displaced_permutation(params) -> dict[str, Any]:
    n = params["n"]
    banned = set(params["banned_displacements"])
    q, r = params["q"], params["r"]
    steps = 0
    solutions = 0
    witness: list[int] | None = None
    cap_hit = False
    for perm in permutations(range(n)):
        steps += 1
        if steps >= _ENUM_CAP:
            cap_hit = True
            break
        displacements = [abs(value - index) for index, value in enumerate(perm)]
        if any(d == 0 for d in displacements):
            continue
        if set(displacements) & banned:
            continue
        if sum(displacements) % q != r:
            continue
        solutions += 1
        if witness is None:
            witness = list(perm)
    return {
        "search_space_size": math.factorial(n),
        "search_space_note": f"{n}! permutations of 0..{n - 1}",
        "candidates_enumerated": math.factorial(n),
        "enumeration_steps": steps,
        "enumeration_cap": _ENUM_CAP,
        "cap_hit": cap_hit,
        "solutions_found": solutions,
        "witness": witness,
    }


_BRUTE_FORCE = {
    "sidon_residue": _brute_sidon,
    "forbidden_words": _brute_forbidden_words,
    "displaced_permutation": _brute_displaced_permutation,
}


# --- parameter randomization --------------------------------------------------

def _params_sidon(rng: random.Random) -> dict[str, Any]:
    n = rng.choice((5, 6))
    m = rng.randint(14, 17) if n == 5 else rng.randint(20, 24)
    q = rng.randint(3, 5)
    return {"n": n, "m": m, "q": q, "r": rng.randrange(q)}


_WORD_POOL = ("000", "111", "0101", "1010", "1001", "0110", "0011", "1100", "010", "101")


def _params_forbidden_words(rng: random.Random) -> dict[str, Any]:
    n = rng.randint(14, 17)
    k = rng.randint(n // 2 - 1, n // 2 + 1)
    forbidden = sorted(rng.sample(_WORD_POOL, rng.choice((3, 4))))
    return {"n": n, "k": k, "forbidden": forbidden}


def _params_displaced_permutation(rng: random.Random) -> dict[str, Any]:
    n = rng.choice((7, 8))
    banned = sorted(rng.sample(range(1, 4), rng.choice((1, 2))))
    q = rng.randint(3, 5)
    return {"n": n, "banned_displacements": banned, "q": q, "r": rng.randrange(q)}


_PARAMS = {
    "sidon_residue": _params_sidon,
    "forbidden_words": _params_forbidden_words,
    "displaced_permutation": _params_displaced_permutation,
}


def _statement(family: str, params: dict[str, Any]) -> str:
    if family == "sidon_residue":
        return (
            f"Construct a list of {params['n']} distinct integers, each in "
            f"[1, {params['m']}], such that (P1) all pairwise sums are distinct "
            f"(Sidon property) and (P2) the total sum is congruent to "
            f"{params['r']} mod {params['q']}.  Submit the list as JSON "
            "(candidate.json)."
        )
    if family == "forbidden_words":
        forbidden = ", ".join(repr(w) for w in params["forbidden"])
        return (
            f"Construct a binary string of length {params['n']} with (P1) exactly "
            f"{params['k']} ones and (P2) none of the forbidden substrings "
            f"{forbidden} occurring anywhere.  Submit the string as a JSON string "
            "(candidate.json)."
        )
    if family == "displaced_permutation":
        banned = ", ".join(str(b) for b in params["banned_displacements"])
        return (
            f"Construct a permutation p of 0..{params['n'] - 1} such that (P1) p "
            f"has no fixed point, (P2) no index i has |p[i] - i| in {{{banned}}}, "
            f"and (P3) the sum of |p[i] - i| over all i is congruent to "
            f"{params['r']} mod {params['q']}.  Submit p as a JSON list "
            "(candidate.json)."
        )
    raise ValueError(f"unknown family {family!r}")


# --- problem assembly -----------------------------------------------------------

@dataclass(frozen=True)
class ConstructionProblem:
    problem_id: str
    family: str
    seed: str
    attempt: int
    params: dict[str, Any]
    statement: str
    checker_source: str
    check_spec: CheckSpec
    brute_force: dict[str, Any]

    @property
    def witness(self) -> Any:
        return self.brute_force["witness"]

    def public_json(self) -> dict[str, Any]:
        """Problem-facing description: statement + parameters + the pinned
        CheckSpec shape.  Checker bytes and answer key stay sealed; only the
        checker blob digest is visible (hash-visible per spec §10.5)."""

        return {
            "schema": "e31-construction-problem-v1",
            "generator_version": GENERATOR_VERSION,
            "id": self.problem_id,
            "family": self.family,
            "seed": self.seed,
            "attempt": self.attempt,
            "parameters": self.params,
            "statement": self.statement,
            "check_spec": self.check_spec.model_dump(mode="json"),
            "candidate_file": "candidate.json",
        }

    def sealed_answer_key(self) -> dict[str, Any]:
        """Witness + brute-force census: sealed, revealed only post-hoc."""

        return {
            "schema": "e31-construction-certificate-v1",
            "generator_version": GENERATOR_VERSION,
            "id": self.problem_id,
            "family": self.family,
            "seed": self.seed,
            "attempt": self.attempt,
            "parameters": self.params,
            "brute_force": self.brute_force,
        }


def check_candidate(problem: ConstructionProblem, candidate: Any) -> tuple[bool, str]:
    """In-process trusted check (same function the sealed script embeds)."""

    return _CHECKERS[problem.family](problem.params, candidate)


def generate_construction(
    seed: int | str, family: str, index: int, *, max_attempts: int = 64
) -> ConstructionProblem:
    """Deterministically generate a solvable construction problem.

    Unsolvable or too-easy parameterizations (no witness, or more than 5% of
    the enumerated space passing) are rejected; the accepted attempt number is
    recorded in the problem metadata.
    """

    if family not in _CHECKERS:
        raise ValueError(f"unknown family {family!r}")
    problem_id = f"e31-constr-{index:03d}"
    for attempt in range(max_attempts):
        rng = random.Random(f"{GENERATOR_VERSION}:{seed}:{family}:{index}:{attempt}")
        params = _PARAMS[family](rng)
        brute = _BRUTE_FORCE[family](params)
        if brute["witness"] is None or brute["cap_hit"]:
            continue
        if brute["solutions_found"] > 0.05 * brute["candidates_enumerated"]:
            continue  # lookup-trivial parameterization; regenerate harder
        checker_source = render_checker(family, params, problem_id)
        ok, reason = _CHECKERS[family](params, brute["witness"])
        if not ok:  # brute force and checker must agree on the witness
            raise RuntimeError(
                f"brute-force witness rejected by trusted checker for "
                f"{problem_id}: {reason}"
            )
        check_spec = CheckSpec(
            id=f"{problem_id}-check",
            runner="command",
            argv=("python3", "checker.py", "candidate.json"),
            cwd=".",
            step_or_item_limit=_ENUM_CAP,
            expected_exit=0,
        )
        return ConstructionProblem(
            problem_id=problem_id,
            family=family,
            seed=str(seed),
            attempt=attempt,
            params=params,
            statement=_statement(family, params),
            checker_source=checker_source,
            check_spec=check_spec,
            brute_force=brute,
        )
    raise RuntimeError(f"no solvable {family} parameterization for seed {seed!r}")
