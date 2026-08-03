# Delivered: "create a skill for less intelligent LLMs ask the right questions in relation to this harness"

Branch: `claude/handover-defect-audit-33pv3d` (pushed, tree clean; head is
the commit carrying this file).

## What changed

A new skill exists: `.claude/skills/dr-ask-the-right-question/SKILL.md` —
question discipline for any model working this repo. It teaches the layer
the two workflow families assume but never state: route every question to
the cheapest authority first (the record, then the framework, then the
operator); translate this operator's terse idiom into typed obligations
via a table whose every row cites a real committed exchange; interrogate
evidence with a fixed diagnostic sequence before theorizing; derive the
operator's answer from their recorded values before spending their
attention (the dominance test, absorbed with credit from the abandoned
`dr-decide-or-ask` lineage, kw8imd 86f1248e); frame genuine uncertainty as
W/R-style falsifiable forks; and avoid six wrong questions this repo has
already paid for, each cited to its errata entry or trap. It is wired in
at the four load-bearing ask-points: both orchestrators route their
stop-and-ask through it, `dr-spec-change` filters its operator-question
batch through it, and CLAUDE.md names it as cutting across both families.
No `src/` file changed; the gate (3290 passed, 0 failed) and all five
docs_verify modes prove it.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "create a skill for less intelligent LLMs ask the right questions" | done | commit b66b7f52; VALIDATION S1 (6 sections, frontmatter loads — it registered in this session's own skill list) |
| R2 | "take a look over the current framework" | done | SPEC.md "The survey (R2)": the two families are phase machinery; the gap is the ask-layer between operator words and phase artifacts; VALIDATION S3 |
| R3 | "reasoning gap that can make the LLM think about the right things" | done | skill sections 1, 3, 5, 6 (authority ladder, record-first sequence, falsifiable forks, wrong-question table); VALIDATION S1 |
| R4 | "other LLMs don't seem to understand my questions and requests like you do" | done-with-assumption A1 | skill section 2: the operator-idiom translation table — "Do it", "as you go" grants, questions-as-prompts, typo resolution — every row citing a committed exchange from this session's tranches |
| R5 | "Ensure its integrated tightly into the current framework" | done-with-assumption A2 | commit b4141169; VALIDATION S2 (both orchestrators + dr-spec-change + CLAUDE.md all reference it) |

## Assumptions the operator may override

- A1: "the right questions" spans three addressees — record, framework,
  operator, in cost order — with operator comprehension as its own
  section. (Q1)
- A2: integration mechanism = cross-cutting subskill + four-file wiring,
  not a third workflow family, not a bare document. (Q2)
- A3: audience = future agent sessions operating this repo through
  `.claude/skills/`; the provider model (glm-5.2) is prompted through the
  packs subsystem and is out of scope. (Q3)
- A4: `dr-decide-or-ask` (kw8imd) absorbed as credited prior art, its file
  not resurrected. (Q4)

## Map delta

No map change — this tranche altered no `src/` behaviour, and
`.claude/skills/` is outside `docs/map/`'s charter. Stated so its absence
is unambiguous. docs_verify: 0 failed / 0 audit findings / 0 dangling /
0 coverage findings; the four `--stale` entries all point at the PREVIOUS
tranche's own commit and are dismissed in VALIDATION.md (stamp lags parent
by construction). New checks: none in the map; the skill's shape is pinned
by VALIDATION S1's grep set.

## Parked (not done, not promised)

- A docs_verify mode that runs `check:` lines inside `.claude/skills/` —
  candidate ratchet so skill claims decay as loudly as map claims.
- Provider-side (packs) question discipline for glm-5.2 — different,
  frozen-adjacent surface.
- Resurrecting the kw8imd paper-trail push hook (db8bfc18) — related
  hygiene, separate decision.
