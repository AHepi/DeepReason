# Validation for: T7 — the measure (S12)
Sub-tranche T7 of the mini isolation programme, the last. Phase:
`dr-validate-change`. Base: `c66aad16b` (T6's delivery head) for this
sub-tranche; `14cc5da495` (main, carrying T2) for the programme's `src/`
reach. Branch: `claude/mini-isolation-t3-t5-7tsc6d`. Run 2026-09-06 under
REQUEST.md Amendment 3 ("go for it jack!"), credential in the gitignored
`env`, never committed, never quoted.

T7 changes no code. It sealed a pre-registration, ran two arms, judged them
blind, and wrote the result down as it came out.

## Acceptance checks

**S12 accept 1** — `PREREG_D8.md` committed with its criteria BEFORE any arm
runs; its sha recorded in RESULTS.md.

    $ git log --format='%h %s' -- experiments/.../PREREG_D8.md | tail -1
    f1b47d270 T7 step 52: seal PREREG_D8.md (the measure) and its instruments; no arm has run
    $ git show f1b47d270 --format=%b -s | grep sha256
    PREREG_D8.md sha256 fedc813eb1afc2759e55fd4ba50748b990ac2e3946a77aa7adf18858b4d2265c
    $ sha256sum PREREG_D8.md   -> fedc813e...  (unchanged since)
    $ grep -c fedc813eb1afc2759e55fd4ba50748b990ac2e3946a77aa7adf18858b4d2265c RESULTS.md  -> 1
    first provider call from this tranche: the probe, commit 5ac96987a (after f1b47d270)
    first ARM call: 04:07:42Z, commit c69129453

: **PASS**.

**S12 accept 2** — RESULTS.md carries both arms' typed outputs, the blind
judging output, the length distributions, and per-seat spend.

    RESULTS.md §2 (ARM 0 table; ARM M terminal block), §3 (BLIND_JUDGING_RESULT_V1
    and the per-candidate table), §4 (D8_LENGTH_HELD_CONSTANT_V1, five sections),
    §5 (D8_PER_SEAT_SPEND_V1, cross-check 39577 == 39577)

: **PASS**.

**C6** — the honesty rule: an inconclusive result recorded as inconclusive,
no arm re-run for a number.

    verdict as the sealed rule fired: INDISTINGUISHABLE; RESULTS.md reads it as a
    NULL result under C6 (improvement not shown), states what it does not mean,
    and lists eight residue entries. ARM 0: exactly 3 calls; ARM M: exactly 1
    root; both committed as they completed. The one exploratory pass is labelled
    NOT pre-registered in its script, its output and RESULTS.md §7.

: **PASS**.

## Full gate

    $ python -m pytest tests/ -q -n 4        (idle box; the arms and the judging were over)
    5084 passed, 6 skipped in 1205.44s (0:20:05)     -> gate rc=0, 0 failed
    $ python -m pytest mini/tests/ -q
    164 passed, 1 skipped in 13.53s

: **PASS** — the same 5084 as T2 through T6; no code changed in T7.

## Record-behavior preservation

T7 changes no reader, writer or validator. ARM M's root verifies (0
violations) and replays (digest equal), the same instruments T6 ran:

    $ git diff --stat c66aad16b..HEAD -- src/ mini/ tools/ scripts/ docs/map pyproject.toml
    (no output)

## Frozen-surface diff

    $ git diff --stat 14cc5da495..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/ \
        src/deepreason/llm/firewall.py
    (no output)

: **PASS** — the whole programme, T0 through T7, moved no frozen surface.
The programme's reach into `src/` is still one file, 29 lines
(`git diff --stat 14cc5da495..HEAD -- src/`).

## Packaging surface

Nothing under `src/` changed since T6 ran both wheel smokes green
(T6/VALIDATION.md); no pin could have moved. Not re-run.

## Map

No map document changed in T7 and no behaviour changed, so no check is
owed. The full `docs_verify` run T5 recorded covers this tree (T6 showed the
only later edits were two stamp lines). `--links` not re-run: no `DR-`
reference was added.

## Requirement sweep

R1–R14, R-stored, R-again, R-history: dispositions as T5/DELIVERY.md and
T6 confirm. R15 (Amendment 2, "Do T6"): done at T6. **R16 (Amendment 3,
"go for it jack!")**: done — T7 executed in this window with the operator's
credential, steps 52–57.

## Assumptions carried

A1–A9 as before. New, T7's own, each stated in PREREG_D8.md before launch:
the model is qwen3.5:397b with reasoning off (comparability with the copied
panel); K = 3 single calls; the judged unit for ARM M is one conjecture;
ARM M runs through the disclosed reasoning-field override (P10).

## Budget

T7 owes no diff under `mini/minireason/` or `src/`. SPEC's 80 for S12 was
for the recording; the tranche adds PREREG_D8.md, RESULTS.md, `d8/` (eight
scripts and their outputs), the two roots, and the blind files.

## Verdict: PASS
