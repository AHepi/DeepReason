# Request: promote the rung-4/5 guardrails into the general workflow

Captured: 2026-08-04, from the operator's exchange with the monitoring
session after rung 3 delivered.

## Verbatim

> Ok. Since you needed guardrails for rung 4 and 5, is there anything to
> add to workflow. Remember it's for general use?

The monitor proposed four additions (each generalizing a recorded catch:
X9/XE1, X11/E10, 55b16ce9, and rung 4's reader-before-writer clause).
The operator's answer:

> do it

## Requirements

R1: dr-spec-change gains a mandatory frozen-surface contact forecast —
declare expected contact against INV-frozen-surfaces.md's list at spec
time; predicted contact stops the tranche for operator words BEFORE
planning. (Evidence: X9, XE1.)

R2: dr-spec-change gains a reachability rule — any mechanism the request
NAMES (fixture, file, pattern) is a suggestion the spec must verify
actually reaches the changed code; unreachable = written fork, never
silent adoption or silent deviation. (Evidence: E10/Q3, X11.)

R3: dr-drive-harness gains the docs-gate rule — iterate with
docs_verify --fast, but the full mode must run once before any commit
touching src/, because --fast reuses cached results and cannot catch
newly-broken documents. (Evidence: 55b16ce9.)

R4: dr-spec-change gains the reader-before-writer guardrail for
record-shape changes — the absence-tolerant reader lands first; every
existing root stays valid before the writer emits. (Evidence: rung 4's
guardrail text; X8.)

## Constraints

C1: skills/docs only; zero src/ or tests/ lines.
C2: each addition cites its errata/commit evidence inline.
C3: push to BOTH branches (operator's standing sync instruction).
