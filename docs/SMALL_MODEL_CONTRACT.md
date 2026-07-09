# Small-Model Skeleton Contract (proposal)

*Derived from the full-harness synthesis frontier
(`experiments/results/impl_synth_frontier.md`, survivors `f12d62f0`,
`8a111ca1`, `06bd67a1`). These are surviving conjectures, not a validated
change — this doc is the buildable spec they imply, to be tested against
the ~10B valid-admission baseline (0.35) before adoption. Nothing here is
wired into `minireason/` yet.*

## Problem

The conjecturer must return, in one call, a nested JSON "skeleton" whose
`forbidden` cases each carry a Python predicate string
(`minireason/loop.py:_prompt`, `minireason/checks.py`). A ~10B model has
the *ideas* but fails the *form* two ways (measured, `runs/nemotron12b`):

- **Structural:** it cannot keep deeply nested JSON well-formed — premature
  object close, missing delimiters, unescaped quotes. **64% of its
  candidates were thrown out on this alone.**
- **Predicate language:** it writes the `eval` in JavaScript or with
  undefined names, so the check errors and self-refutes the candidate.

Both are *formatting* failures, not reasoning failures. The fix must move
structural well-formedness off the model onto deterministic harness
machinery **without** changing what the model must think — critically,
the model still authors its own `claim`, `mechanism`, and `forbidden`
cases (the operator ruling: commitment generation is untouched).

## Invariants this must preserve (non-negotiable)

1. The LLM stays a **bounded pure function** `pack -> text`; it holds no
   graph state, adjudicates nothing, controls no flow.
2. **Determinism / byte-exact replay:** the harness logs the raw model
   text; every transform from raw text to skeleton is a pure function, so
   replay re-derives the identical skeleton.
3. **Commitment generation intact:** the model authors every `forbidden`
   case (the prose *and* the predicate) in the same call. The design only
   changes the *shape* it writes, never *what* it must produce. (R2 out.)
4. **Measures never adjudicate:** the new checks are well-formedness gates
   (like `skeleton-wf` today), not adjudication.

## The contract

### Tier A — flat wire format + deterministic expander + predicate anchor
Works on **any** OpenAI-compatible provider. This is the baseline.

**A1. The model emits a FLAT, line-oriented record — no nesting.**
Instead of nested JSON, each candidate is lines of `key: value`:

```
claim: <one clause>
mechanism: <how it works>
covers: <case>; <case>
excludes: <case>
forbid: <refuter prose> || content -> <python bool expression>
forbid: <refuter prose> || content -> <python bool expression>
```

There are no brackets to balance and no nesting to track — the failure
mode that killed 64% of candidates is **unrepresentable**. `forbid` lines
repeat; each pairs the refuter prose with its predicate after `||`.

**A2. A deterministic harness-side expander assembles the skeleton.**
`expand_flat(text) -> dict` (pure, no LLM, no wall-clock) parses the lines
into the exact skeleton dict the rest of the harness already consumes:

```python
{"claim": str, "mechanism": str,
 "scope": {"covers": [...], "excludes": [...]},
 "forbidden": [{"case": str, "eval": "predicate:<expr>"}, ...],
 "prose_notes": str}
```

Downstream is **unchanged**: `parse_skeleton`, the gate, `compile_checks`,
criticism, adjudication all see the same dict as today. A missing required
line ⇒ the existing `skeleton-wf` refutation (now a *semantic* failure —
"no mechanism" — never a *syntactic* one — "unbalanced brace").

**A3. Predicate language is anchored and checked at admission.**
The `content ->` prefix names the language unambiguously (a Python
expression over the string variable `content`). Before a candidate is
admitted, the harness runs `ast.parse(expr, mode="eval")` (the machinery
already exists in `checks._validate_predicate`) and **rejects any predicate
that is not a valid Python expression** — JavaScript, undefined-name calls,
and statements all fail here with a logged reason. A candidate whose only
forbidden cases are rejected forbids nothing ⇒ refuted on arrival (existing
rule). The JS-predicate failure is caught at the door, not after it
silently self-refutes.

### Tier B — constrained decoding (optional, provider-permitting)
Where the provider exposes grammar-guided decoding (llama.cpp GBNF, vLLM
`guided_grammar`, Outlines) — i.e. local/self-hosted small models, the
realistic ~10B deployment — attach a grammar for the flat format so a
malformed line is **impossible to emit**, not merely rejected after the
fact. This is survivor `f12d62f0`'s resolution of the R1a/R1b conflict:
the grammar owns the *outer* line structure; the free-text `value` regions
(including any placeholder-ish content) are unconstrained, so the two
mechanisms cooperate instead of fighting. Tier B is belt-and-suspenders on
top of Tier A; Tier A alone already removes the structural failure.

## Where each piece sits in the loop

| step | today | proposed |
|---|---|---|
| γ-call prompt | nested-JSON skeleton dump | flat-format instructions + one filled example |
| model returns | nested JSON string | flat `key: value` text (logged raw, as now) |
| admission | `parse_skeleton` (JSON) | `expand_flat` (pure) → same dict, then `ast.parse` each predicate |
| gate / checks / criticism / adjudication | — | **unchanged** |

## Concrete code delta (MiniReason)

- `minireason/loop.py:_prompt` — replace the nested-JSON instructions with
  the flat format + one worked example (including a real Python predicate
  like `content -> len(content) > 120`).
- `minireason/checks.py` — add `expand_flat(text) -> dict | None` (pure);
  call it inside `parse_skeleton` before JSON fallback; promote
  `_validate_predicate` from a safety gate to an **admission** check whose
  rejection is logged as a `gate:bad-predicate` measure.
- `minireason/call.py` — the γ schema wraps flat text; no change to the
  meter, repair loop, or blob logging (the raw flat text is the blob).
- `minireason/{gate,log,rotate,judge}.py` — **no change.** They operate on
  the assembled skeleton, which is byte-identical to today's.

## Forbidden cases (how to refute THIS design)

Per the harness ethic, the spec states what would kill it:

- **F1 (purity):** if `expand_flat` is not a pure function of the logged
  text (any order- or environment-dependence), byte-replay diverges on an
  existing root ⇒ the design breaks the determinism invariant ⇒ refuted.
- **F2 (payoff):** if, on a fresh ~10B run, valid-admission rate does not
  rise materially above the measured **0.35** baseline (target: clear
  0.80, matching the strong-model rate), the flat format did not earn its
  keep ⇒ refuted.
- **F3 (expressiveness):** if any skeleton the nested contract can express
  cannot be represented in the flat format (e.g. nested scope structures),
  the format is lossy ⇒ refuted, or scope must be restricted and that
  restriction measured.
- **F4 (predicate false-negatives):** if the `ast.parse` admission gate
  rejects legitimate predicates a strong model writes today (regression on
  a committed root's predicates), the anchor is too strict ⇒ refuted.

## Test plan (before any adoption)

1. Build Tier A behind a flag; keep the nested path as control.
2. Re-run the `nemotron12b` battery flat-vs-nested at matched budget;
   compare valid-admission and survivors-per-token (F2).
3. Byte-replay a committed strong-model root through `expand_flat` to
   confirm F1 and F4 (no divergence, no legitimate-predicate regression).
4. Only then propose the `minireason/` change, citing the numbers.
