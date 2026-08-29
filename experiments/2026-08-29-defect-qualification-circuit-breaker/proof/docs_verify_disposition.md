# docs_verify disposition — lane C

    $ python tools/docs_verify.py
    docs_verify [full]: 70 documents, 1247 checks, 4 workers
    docs_verify: 9 failed

Raw transcript: `docs_verify.out`.

**9 failed is the baseline for a SHALLOW clone, and this container is one**
(`git rev-parse --is-shallow-repository` -> `true`). `docs/AUDIT_BASELINES.md`
states 6 expected failures on a full clone and 9 on a shallow one, itemised by
class. **Delta zero.** Each observed failure against its baseline row:

| observed | baseline row | class |
|---|---|---|
| `SEAM-llm-x-verification.md:19` | same | claim rotted (P1) |
| `INV-frozen-surfaces.md:657` | same | stale qualification-digest pin (P2) |
| `SEAM-llm-x-rules.md:54` | same | check malformed (P3) |
| `INV-signal-contract.md:243` | listed at `:222` | check imprecise (P4) — `LINEAGE_POLICIES` in a COMMENT |
| `CON-discharge-channel.md:150` | same | check unreachable (P5) |
| `INV-frozen-surfaces.md:181` | same | falsified census, pre-existing |
| `CON-run-identity.md:211`, `:213`, `:215` | listed at `:200/202/204` | shallow clone only — the three git-history checks |

Four line numbers moved because those documents grew on `main`; the checks
and their classes are the same ones. No new failure, and no different one.

## One observation this tranche owes the record, and did not cause

`AUDIT_BASELINES.md` states the instrument's size as **"1212 checks over 69
documents"**. On `main` at `facea8f81` the corpus already holds **70
documents and 1246 column-0 `check:` openers**, so the stated size is stale
by roughly 34 checks and one document — almost certainly the batch's own Lane
D seam document plus subsequent growth, recorded after the re-baselining
sentence was written.

Measured, so the attribution is not a guess:

    $ git archive facea8f81 docs/map | tar -xO | grep -c '^`check:'
    1246
    $ cat docs/map/*.md | grep -c '^`check:'
    1248

**+2, and both are this tranche's** — one new `Traps` check in `SUB-llm.md`
(21 -> 22 openers) and one in `SUB-manifest.md` (19 -> 20). Nothing else in
the corpus was touched:

    $ git diff --name-only 08c2d7bd1 70fdef7e6 -- docs/
    docs/map/SUB-llm.md
    docs/map/SUB-manifest.md

The FAILURE set is what the baseline exists to pin, and it matches exactly.
The stale COUNT is a docs-drift finding against `AUDIT_BASELINES.md` itself;
it is parked, not fixed here, because that file is outside this cone.

## Both new checks are failable, and were proven so before being written down

`docs_verify --audit` refuses checks that cannot fail. It reports exactly one
finding, the pre-existing `SEAM-llm-x-rules.md:54` unparseable opener (P3).

Each new check was additionally mutation-proven by hand — green on the clean
tree, red under a mutation of the behaviour it claims, green again after
restore, with `cmp` confirming the tree byte-identical afterwards:

| mutation | check | verdict |
|---|---|---|
| delete the `http_status` branch from `_failure_code` | `SUB-llm.md` | exit 1 |
| `EndpointError` exposes a numeric `.code` | `SUB-llm.md` | exit 1 |
| `_QualificationCircuit.key` returns a constant (global keying) | `SUB-manifest.md` | exit 1 |
| delete the short-circuit from `_case_block` | `SUB-manifest.md` | exit 1 |
