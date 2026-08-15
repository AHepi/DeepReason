# SPEC — Rung 3c

Traces to REQUEST.md C1–C9. **Diff budget: 700 lines** — production 380,
tests 250, map + docs 70.

## Shape

A new package, `src/deepreason/calculus/`, with the advice's boundary:

| file | owns |
|---|---|
| `claims.py` | the CLOSED union of versioned bodies, and their canonical encoding |
| `compiler.py` | the ONLY translation from a body to an `Interface` |
| `programs.py` | the structural well-formedness programs those bodies carry |
| `operations.py` | `ensure_problem_subject` — two-step, idempotent |
| `views.py` | `problem_status`, `problem_subject_missing` — derived, never stored |

## D1 — the union is closed at the SCHEMA NAME, and only built where there is a producer

`CLAIM_SCHEMAS` is a closed `Literal` over the advice's nine names, so nothing
outside it can ever decode. **Bodies are implemented for the two that have a
producer in this rung** — `poietic.problem-subject.v1` and
`poietic.premise-attribution.v1`. The other seven are declared and
unimplemented, and `decode` refuses them with a typed
`claim-schema-not-implemented` rather than silently accepting.

That split is deliberate. Shipping nine body models with no producers is the
E28 pattern this program has now paid for three times — a mechanism nobody
triggers. Closing the NAME set is what R60 actually asks for: it is what stops
arbitrary prose predicates becoming quasi-ontology, and it does not require the
bodies to exist yet.

## D2 — the six recognition conditions, all required

An artifact is a problem subject only when every one holds:

1. the canonical body parses,
2. `problem_id` resolves to a registered `Problem`,
3. the copied `description`, `criteria`, `trigger` and `sources` MATCH that
   record exactly,
4. the required structural commitment is present,
5. the artifact ADDRESSES that problem,
6. the interface contains ONLY the permitted refs.

Condition 3 is the one carrying the weight: without it a companion could drift
from its problem and criticism would land on a stale copy. Conditions 4–6 are
what make recognition structural (C3 dispatch on interface) rather than a
`kind` field.

## D3 — determinism and idempotence

The companion body is a pure function of the `Problem` record, so its content
address is too: calling `ensure_problem_subject` twice registers one artifact
and commits one event the first time and none the second. That is what makes
the crash gap recoverable — resume simply calls it again.

`problem_subject_missing(harness)` is the typed diagnostic: registered problems
with no recognised companion. A crash between the two writes shows up there and
is repaired by re-running the operation, never by changing event atomicity.

## D4 — what this rung deliberately does NOT do

- **No scheduler integration** (C8). Nothing selects on `problem_status`.
- **No retrofit of the premise channel.** `premises.py` keeps working exactly
  as delivered; the union carries a `poietic.premise-attribution.v1` body that
  compiles to the same interface shape, and MOVING the channel onto it is a
  later step with its own regression obligations.
- **No synthesizer change** (C9).
- **No fields on `Problem`/`EpistemicState`/`Event`** (C5).

## Acceptance checks

| # | Check |
|---|---|
| D-a | An open predicate cannot enter: `decode` refuses an unknown schema name, and the union's name set is closed |
| D-b | Each of the six recognition conditions, broken one at a time, makes recognition FAIL |
| D-c | `ensure_problem_subject` is idempotent: twice ⇒ one artifact, one event |
| D-d | The compiled interface has exactly the permitted refs with the roles the CONTROLLER chose; no body field names a role |
| D-e | A premise-attribution body compiles to `mention` on the premise — never `dependence` — the mention law, now enforced at compile time |
| D-f | Attacking a companion changes `problem_status` and nothing else; the `Problem` record is untouched |
| D-g | `problem_subject_missing` names a problem whose companion was never written, and re-running the operation clears it |
| D-h | `Problem`, `EpistemicState` and `Event` gained no field |
| D-i | Full gate 0 failed; `docs_verify` full at the recorded baseline; map in the same commit |
