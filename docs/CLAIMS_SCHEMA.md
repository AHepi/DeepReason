# The claims file — pre-registered universal statements, tested against a record

A CLAIM is a universal statement about what a run DID: "the critic never
exhausts its smallest authorized contract", "every conjecturer section plan
names the organiser's output contract". You write it down before you look,
and one run record can refute it.

`tools/record_claims.py` reads one or more run roots and a claims file, and
prints, for each claim, whether any supplied record refuted it, which records
did, and — when none did — whether the records could have. Nothing is
written; no status changes; nothing is scored. The output is an instrument
for a tranche's RESULTS.md.

The shape is adopted from the operator's other harness (h-EPI,
`src/creib/forge/conformance/claims.py`, read at commit `f97239fc`); the
vocabulary below is DeepReason's own, over the fields the record already
carries. No code was copied.

## What this is NOT

- **Not a gate.** The command exits 0 whether every claim is refuted or none
  is. It exits non-zero only when it cannot do its job: a claims file that
  does not validate, a root it cannot read, a usage error.
- **Not a status.** It never writes into a run root, never appends to
  `log.jsonl`, and never changes an artifact's Status. It imports nothing
  from `src/deepreason/`, so no path exists by which it could.
- **Not a score.** Counts are of records, not of quality. A claim refuted by
  three records is not "worse" than one refuted by one, and a survival ranks
  nothing.
- **Not an appraisal.** The operator's other harness carries a second layer
  that labels arguments in, out or undecided and takes each argument's
  readiness FROM A PERSON. That layer is not adopted here and its readiness
  rule is explicitly rejected: in DeepReason, whether a criticism carries
  authority is the harness's own decision, read from the record — warrant
  checks, judge verdicts, criticism dispatch — never marked by a person.
  There is no readiness field in this schema and no place to put one.

## The file

```json
{
  "schema_version": "deepreason.record-claims.v1",
  "title": "Conjectures about what the organiser seat did",
  "claims": [
    {
      "claim_id": "CRIT-CAP-01",
      "statement": "The argumentative critic seat never terminally exhausts its smallest authorized contract.",
      "kind": "never",
      "scope": {"states": ["failed", "completed"]},
      "condition": {
        "object": {
          "kind": "workflow-route-seat-insufficient-capability-v1",
          "where": [
            ["route_lease.role", "eq", "argumentative_critic"],
            ["reason", "eq", "smallest_authorized_contract_schema_exhausted"]
          ]
        }
      },
      "note": null
    }
  ]
}
```

`schema_version` must be exactly `deepreason.record-claims.v1`. `title` is
optional. `claims` is a non-empty list. Every `claim_id` is unique and
matches `^[A-Za-z][A-Za-z0-9._-]{0,63}$`.

Per claim: `claim_id`, `statement` and `kind` are required, `condition` is
required, `scope` and `note` may be absent or null. Any other key is refused.

## The unit of observation is one run root

Everything is counted in run roots. A root is a directory holding
`run-status.json`, `log.jsonl` and `objects/`. Its identity for reporting is
`run_id` from `run-status.json`, falling back to the directory's own name.

## Kind

| kind | refuted by |
|---|---|
| `never` | one root where the condition HOLDS |
| `always` | one root where the condition DOES NOT hold |

## Scope

`scope` selects which roots the claim is TESTED on. Every key present and
non-null must match; an absent or null key matches anything.

| key | matched against |
|---|---|
| `run_ids` | `run-status.json` `run_id` |
| `root_names` | the root directory's basename |
| `states` | `run-status.json` `state` |
| `stop_reasons` | `run-status.json` `stop_reason` |
| `workloads` | `run-status.json` `workload` |

Roots the scope excludes are still READ — they are what the standing is
computed from.

## Conditions

A condition is an object with EXACTLY ONE key. An unknown key raises; it
never quietly evaluates to false. This is the fail-closed rule: a typo in a
condition must stop the run, not turn into a survival.

### Nesting

| key | value |
|---|---|
| `all_of` | non-empty list of conditions; holds when every one holds |
| `any_of` | non-empty list of conditions; holds when at least one holds |
| `not` | one condition; holds when it does not |

### `status` — one field of `run-status.json`

```json
{"status": {"field": "stop_reason", "in": ["operational_failure"]}}
{"status": {"field": "cycle", "lt": 4}}
{"status": {"field": "terminal_lifecycle_refusal", "present": true}}
```

`field` is a top-level key of `run-status.json`. Exactly one comparison:
`eq`, `ne`, `in`, `not_in`, `contains`, `gt`, `gte`, `lt`, `lte`, `present`
(a boolean), `absent` (a boolean). A field the root does not carry compares
false for everything except `absent: true` and `present: false`.

**A field name nobody's record carries is caught by the standing, not by an
error.** If you write `stop_resaon`, no root can ever satisfy the condition,
the claim survives, and the standing says the refuting condition held on no
supplied root at all. That is the sentence to read before trusting the
survival.

### `event` — a count of log events by rule

```json
{"event": {"rule": "Crit", "min_count": 1}}
```

`rule` is one of the record's own rule names: `Conj`, `Crit`, `Adj`, `Spawn`,
`Refl`, `Register`, `Merge`, `Measure`, `Reveal`, `Reseed`, `Scratch`,
`Bridge`, `ConjectureTurn`, `Control`, `Capability` (`DR-SUB-harness`;
`src/deepreason/ontology/event.py`). Any other name raises.
`min_count` defaults to 1.

### `measure` — a count of `Measure` events by their measure code

A `Measure` event names its code in `inputs[0]`.

```json
{"measure": {"code": "criticism.dispatch.v1"}}
{"measure": {"code_prefix": "evidence-citation:", "min_count": 1}}
```

Exactly one of `code` and `code_prefix`. `min_count` defaults to 1.

### `control` — a count of `Control` events by their action

A `Control` event carries `control.action` (`control.event.v3`).

```json
{"control": {"action": "lifecycle_stopped"}}
```

`min_count` defaults to 1.

### `object` — a count of records under `objects/<kind>/`

```json
{"object": {"kind": "workflow-context-section-plan-v1",
            "where": [["layout_id", "eq", "seat-pack.conjecturer.organiser-v1"],
                      ["every:sections[].plugin_id", "ne", "dr.output-contract.organiser"]],
            "min_count": 1}}
```

`kind` is a directory name under `objects/`. A kind the root does not carry
counts zero — it is not an error, because roots legitimately differ in which
kinds they hold. `where` is a list of `[path, op, value]` triples, all of
which must hold for an object to count; an absent or empty `where` counts
every object of the kind. `min_count` defaults to 1.

**Paths** are dotted, resolved against the object's `data`. `[]` iterates a
list. A path may carry a quantifier prefix:

| prefix | holds when |
|---|---|
| `any:` (the default) | at least one resolved value satisfies the op |
| `every:` | every resolved value satisfies the op |

`every:` on a path that resolves to nothing is TRUE — vacuously. That is
usually what you want (`every:sections[].plugin_id ne X` should hold of a
plan with no sections at all, which certainly does not name X), but it is a
place a claim can survive without meaning to, so it is stated here.

**Ops** are `eq`, `ne`, `in`, `not_in`, `contains`, `present`, `absent`,
`gt`, `gte`, `lt`, `lte`. `contains` is substring for strings and membership
for lists. `present` and `absent` take a boolean and ignore the quantifier:
`present: true` holds when the path resolves to at least one value.
`gt`/`gte`/`lt`/`lte` compare numbers and skip anything that is not one.

## The three statuses

| status | means |
|---|---|
| `REFUTED` | at least one root in scope refuted the claim |
| `UNREFUTED_FOR_DECLARED_SCOPE` | roots were tested and none refuted it |
| `NOT_TESTED` | the scope admitted no supplied root |

`UNREFUTED_FOR_DECLARED_SCOPE` is not a proof and not a confirmation. The
scope is exactly the roots supplied, and the next root may refute it.

## The two standings

A survival is only as good as the check behind it. For every claim the tool
counts how many SUPPLIED roots satisfied the refuting predicate — in scope or
out of it.

| standing | means |
|---|---|
| `SHOWN_ABLE_TO_FAIL` | the refuting condition held on at least one supplied root |
| `NOT_SHOWN_ABLE_TO_FAIL` | it held on none, in or out of scope |

A claim marked `NOT_SHOWN_ABLE_TO_FAIL` names a measure code, an object kind
or a status value that no supplied record ever carried. The records could not
have refuted it whatever the run did. It is still a survival for the declared
scope, and it should be read as a fact about what the records contain, not as
a test the harness passed. The tool prints that sentence rather than leaving
the reader to work it out.

## Running it

```sh
python tools/record_claims.py --claims <claims.json> --root <run root> [--root <run root> ...]
python tools/record_claims.py --claims <claims.json> --root <run root> --json
python tools/record_claims.py --claims <claims.json> --root <run root> --markdown claims.md
```

`--json` prints one object carrying every field the text report shows, for a
RESULTS.md table or a later comparison. `--markdown` writes the report as
markdown to a path OUTSIDE any run root; the tool refuses a path inside one.
`--quiet` suppresses the header and the closing limit.

Refuting record ids are capped at five per claim, with a count of the rest,
and each carries one locator into the record that refuted it —
`run-status.json:<field>=<value>`, `log.jsonl:seq=<n>`, or
`objects/<kind>/<sha>.json`.

## Where the record's vocabulary is documented

- `DR-SUB-harness` — the append-only log, what an event carries, and how
  state is materialized from it.
- `DR-CON-evidence-states` — telling a survivor from an untested conjecture,
  and the declaration that says whether a criticism pass ran in full. A claim
  about "what survived" must read that document first: this tool reports what
  the record says happened, not what it means.
- `DR-INV-evidence-channels` — the three evidence-minting channels and the
  one field that turns any of them off. A claim about citations is a claim
  about a channel that was on.
- `DR-SUB-evidence` — admitted dossiers, admitted blocks, and the eight typed
  citation-check codes.
- `DR-SUB-verification` — `verify_root` and replay validation, which decide
  whether a record is admissible at all. This tool does not run them and does
  not stand in for them.

## The limit, stated once

Every report closes with it: a claim no supplied record refuted is unrefuted
for exactly those records. Survival is not confirmation, counts imply no
ranking, and nothing here treats a survival as evidence for anything.
