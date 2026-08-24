#!/usr/bin/env python3
"""derivation_check.py — deterministic replay of model-proposed derivations.

Usage:
    derivation_check.py RULES.json THEORY.json DERIVATION.json [--lax] [--attest ATT.json]

Exit codes: 0 all steps PASS and conclusion matches target;
            1 any step FAIL (errors are STEP-ADDRESSED for the refine loop);
            3 no FAILs but some CANNOT_VERIFY (manual side conditions) —
              strict acceptance treats this as failure; --lax accepts it
              and the caller must record the grade honestly.

The rule system is DATA (RULES.json), never code: this checker knows only
grammar, matching, substitution, and grade propagation. Authoring the rule
profile from a frozen calculus is a reviewed transcription task, and until
that review the checker's PASS certifies conformance to the TRANSCRIPT,
not to the calculus. A model's failure to find a derivation is never
evidence of non-derivability; that claim belongs to countermodel search.

Formula language: the jacquard s-expression conditions. Rule patterns use
metavariables: strings "?A" match any formula/term consistently; "?x:var"
matches only a ["var", ...] term. Side condition kinds understood:
  {"kind":"substitution","of":"?A","var":"?x","term":"?t","gives":"?B"}
  {"kind":"distinct","vars":["?x","?y"]}
  {"kind":"MANUAL","text":"..."}          -> CANNOT_VERIFY (fail-closed)

RULES.json:
  {"schema":"DERIVATION_RULES_V1",
   "grades":{"order":["D","T","P","B"],"default_propagation":"min"},
   "rules":{"MP":{"premises":[["implies","?A","?B"],"?A"],
                  "conclusion":"?B","side_conditions":[]}, ...}}

DERIVATION.json:
  {"schema":"DERIVATION_V1","theory":"...","target":"<row id>",
   "steps":[{"id":"s1","rule":"PREMISE","row":"AX1","grade":"D"},
            {"id":"s2","rule":"MP","premises":["s1","sX"],
             "formula":[...],"grade":"T"}, ...],
   "conclusion_step":"sN"}
PREMISE steps cite a theory row id; their formula is TAKEN FROM the theory
profile (byte-authoritative), never restated. Steps may cite only earlier
steps. Every non-PREMISE step states its formula explicitly.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def attest_key(rules_sha: str, deriv_sha: str, step_id: str, text: str) -> str:
    """Byte-bound attestation key: any edit to rules or derivation
    invalidates every attestation automatically. Attestations are owner
    provenance (who, when, over which bytes, why) -- never verification."""
    return hashlib.sha256(f"{rules_sha}:{deriv_sha}:{step_id}:{text}".encode()).hexdigest()


def is_meta(x) -> bool:
    return isinstance(x, str) and x.startswith("?")


def match(pattern, formula, binding: dict) -> dict | None:
    """Syntactic match of a rule pattern against a ground formula/term,
    threading one consistent binding map. Returns extended binding or None."""
    if is_meta(pattern):
        name, _, kind = pattern.partition(":")
        if kind == "var" and not (isinstance(formula, list) and formula and formula[0] == "var"):
            return None
        if name in binding:
            return binding if binding[name] == formula else None
        b = dict(binding)
        b[name] = formula
        return b
    if isinstance(pattern, list) and isinstance(formula, list):
        if len(pattern) != len(formula):
            return None
        b = binding
        for p, f in zip(pattern, formula):
            b = match(p, f, b)
            if b is None:
                return None
        return b
    return binding if pattern == formula else None


def instantiate(pattern, binding: dict):
    if is_meta(pattern):
        name = pattern.partition(":")[0]
        if name not in binding:
            raise KeyError(f"unbound metavariable {pattern}")
        return binding[name]
    if isinstance(pattern, list):
        return [instantiate(p, binding) for p in pattern]
    return pattern


def subst(formula, var_name: str, term):
    """Capture-aware substitution [var := term]; refuses (returns None) if a
    binder would capture a variable of the term — fail closed, never rename."""
    def term_vars(t, acc):
        if isinstance(t, list):
            if t and t[0] == "var":
                acc.add(t[1])
            else:
                for x in t[1:]:
                    term_vars(x, acc)
        return acc

    tvars = term_vars(term, set())

    def go(f):
        if isinstance(f, list):
            if f[0] == "var":
                return term if f[1] == var_name else f
            if f[0] in ("forall", "exists"):
                _, v, sort, body = f
                if v == var_name:      # shadowed: substitution stops here
                    return f
                if v in tvars:         # would capture — refuse
                    raise _Capture()
                return [f[0], v, sort, go(body)]
            return [f[0]] + [go(x) for x in f[1:]] if f[0] not in ("elem",) else f
        return f

    class _Capture(Exception):
        pass
    _Capture = _Capture  # local name binding for closure
    try:
        return go(formula)
    except Exception:
        return None


def grade_leq(order: list, a: str, b: str) -> bool:
    return order.index(a) <= order.index(b)


def check(rules_p: Path, theory_p: Path, deriv_p: Path, lax: bool,
          attest_p: Path | None = None) -> int:
    rules_doc = json.loads(rules_p.read_text(encoding="utf-8"))
    theory = json.loads(theory_p.read_text(encoding="utf-8"))
    deriv = json.loads(deriv_p.read_text(encoding="utf-8"))
    rules_sha = hashlib.sha256(rules_p.read_bytes()).hexdigest()
    deriv_sha = hashlib.sha256(deriv_p.read_bytes()).hexdigest()
    attest = {}
    if attest_p and attest_p.exists():
        attest = {a["key"]: a for a in json.loads(attest_p.read_text()).get("attestations", [])}
    audited_steps: set = set()
    errors, cannot = [], []
    if rules_doc.get("schema") != "DERIVATION_RULES_V1":
        errors.append("rules: bad schema")
    if deriv.get("schema") != "DERIVATION_V1":
        errors.append("derivation: bad schema")
    if errors:
        return report(errors, cannot, deriv, lax)

    grades = rules_doc["grades"]["order"]
    rules = rules_doc["rules"]
    rows = theory["rows"]
    steps = deriv.get("steps", [])
    seen: dict[str, dict] = {}

    for i, st in enumerate(steps):
        sid = st.get("id") or f"<step {i}>"
        where = f"step {sid}"
        if sid in seen:
            errors.append(f"{where}: duplicate id")
            continue
        g = st.get("grade")
        if g not in grades:
            errors.append(f"{where}: grade {g!r} not in {grades}")
            continue
        if st.get("rule") == "PREMISE":
            row = st.get("row")
            if row not in rows:
                errors.append(f"{where}: PREMISE cites unknown row {row!r}")
                continue
            st["formula"] = rows[row]["condition"]  # byte-authoritative
            seen[sid] = st
            continue
        rname = st.get("rule")
        rule = rules.get(rname)
        if rule is None:
            errors.append(f"{where}: unknown rule {rname!r}")
            continue
        cited = st.get("premises", [])
        if len(cited) != len(rule["premises"]):
            errors.append(f"{where}: rule {rname} takes {len(rule['premises'])} premises, cited {len(cited)}")
            continue
        prem_steps = []
        bad = False
        for c in cited:
            if c not in seen:
                errors.append(f"{where}: cites {c!r} which is not an EARLIER step")
                bad = True
                break
            prem_steps.append(seen[c])
        if bad:
            continue
        binding: dict | None = {}
        for pat, ps in zip(rule["premises"], prem_steps):
            binding = match(pat, ps["formula"], binding)
            if binding is None:
                errors.append(f"{where}: premise {ps['id']} does not match rule "
                              f"{rname} pattern {json.dumps(pat)}")
                break
        if binding is None:
            continue
        sc_fail = False
        for sc in rule.get("side_conditions", []):
            kind = sc.get("kind")
            if kind == "MANUAL":
                key = attest_key(rules_sha, deriv_sha, sid, sc.get("text", ""))
                if key in attest:
                    a = attest[key]
                    audited_steps.add(sid)
                    cannot.append(f"{where}: HUMAN_AUDITED by {a.get('by')} on "
                                  f"{a.get('date')} -- {a.get('reason', '')[:80]} "
                                  "(provenance, not verification)")
                else:
                    cannot.append(f"{where}: MANUAL side condition unverified: {sc.get('text', '')}")
            elif kind == "distinct":
                vals = [binding.get(v.partition(':')[0]) for v in sc["vars"]]
                if len({json.dumps(v) for v in vals}) != len(vals):
                    errors.append(f"{where}: distinctness side condition violated for {sc['vars']}")
                    sc_fail = True
            elif kind == "substitution":
                A = binding.get(sc["of"].partition(":")[0])
                x = binding.get(sc["var"].partition(":")[0])
                t = binding.get(sc["term"].partition(":")[0])
                if A is None or x is None or t is None:
                    errors.append(f"{where}: substitution side condition references unbound metavariables")
                    sc_fail = True
                    continue
                res = subst(A, x[1], t)
                if res is None:
                    errors.append(f"{where}: substitution would capture a variable — refused")
                    sc_fail = True
                else:
                    binding = match(sc["gives"], res, binding)
                    if binding is None:
                        errors.append(f"{where}: substitution result does not match {sc['gives']}")
                        sc_fail = True
            else:
                cannot.append(f"{where}: unknown side-condition kind {kind!r} — CANNOT_VERIFY")
        if sc_fail or binding is None:
            continue
        try:
            expected = instantiate(rule["conclusion"], binding)
        except KeyError as e:
            errors.append(f"{where}: {e}")
            continue
        if expected != st.get("formula"):
            errors.append(f"{where}: stated formula differs from rule {rname} conclusion "
                          f"{json.dumps(expected)[:120]}")
            continue
        prop = rule.get("grade", rules_doc["grades"].get("default_propagation", "min"))
        if prop == "min":
            # order lists strongest grade first; a derived step is at most as
            # strong as its WEAKEST premise (largest index)
            floor = max((grades.index(p["grade"]) for p in prem_steps), default=0)
            if grades.index(g) < floor:
                errors.append(f"{where}: grade {g} exceeds authority of premises "
                              f"(floor {grades[floor]})")
                continue
        elif prop in grades and g != prop:
            errors.append(f"{where}: rule {rname} fixes grade {prop}, step claims {g}")
            continue
        seen[sid] = st

    # transitive HUMAN_AUDITED taint (sorry-axiom style): any step depending
    # on an audited step is itself at most HUMAN_AUDITED
    tainted = set(audited_steps)
    changed = True
    while changed:
        changed = False
        for st in steps:
            if st.get("id") in tainted:
                continue
            if any(c in tainted for c in st.get("premises", [])):
                tainted.add(st["id"])
                changed = True

    conc = deriv.get("conclusion_step")
    if conc not in seen:
        errors.append(f"conclusion_step {conc!r} is not a checked step")
    else:
        target = deriv.get("target")
        if target not in rows:
            errors.append(f"target {target!r} not a theory row")
        elif seen[conc]["formula"] != rows[target]["condition"]:
            errors.append(f"conclusion formula does not match target row {target} byte-exactly")
    return report(errors, cannot, deriv, lax, audited_steps, tainted)


def report(errors, cannot, deriv, lax, audited=(), tainted=()) -> int:
    for e in errors:
        print(f"FAIL {e}")
    for c in cannot:
        print(f"CANNOT_VERIFY {c}")
    n = len(deriv.get("steps", []))
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s) over {n} step(s))")
        return 1
    unaudited = [c for c in cannot if "HUMAN_AUDITED" not in c]
    if cannot and not unaudited:
        print(f"RESULT: PASS_HUMAN_AUDITED ({len(audited)} attested step(s); "
              f"{len(tainted)} step(s) transitively dependent on human audit -- "
              "this count is the trusted-human base and it grows quietly)")
        return 0
    if cannot:
        print(f"RESULT: CHECKED_EXCEPT_MANUAL ({len(unaudited)} unverified side condition(s)); "
              "grade the record accordingly")
        return 0 if lax else 3
    print(f"RESULT: PASS ({n} step(s) replayed; conclusion matches target)")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    lax = "--lax" in argv
    attest = None
    if "--attest" in argv:
        attest = Path(argv[argv.index("--attest") + 1])
        argv = [a for i, a in enumerate(argv)
                if a != "--attest" and (i == 0 or argv[i - 1] != "--attest")]
    args = [a for a in argv if a != "--lax"]
    if len(args) != 3:
        print(__doc__)
        return 2
    return check(Path(args[0]), Path(args[1]), Path(args[2]), lax, attest)


if __name__ == "__main__":
    sys.exit(main())
