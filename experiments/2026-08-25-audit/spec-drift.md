# Dimension: spec drift (code vs the spec series)

Spec series: `docs/harness-spec-v1.3.md` plus the v1.4, v1.5, v1.6 and
v1.7 amendments. Later files supersede earlier ones on conflict.

## Method reconciliation — read this before comparing to 2026-08-13

The comparison audit's CLI-flag number is only reproducible under its own
matching rule, which it did not state. It matched the flag STEM (the token
with `--` stripped), not the literal `"--flag"` string. Re-deriving:

| matching rule | flags spec-silent |
|---|---|
| literal `--flag` | 74 / 76 |
| stem (`cycles`, not `--cycles`) | **34 / 76** |

34 is exactly the prior audit's published number, so stem matching is its
rule and this audit uses it too. **The 74 is a matching artifact, not a
drift delta** — rowing it would have manufactured a 40-flag regression that
does not exist. Full note: `proof/spec-method.txt`.

Config fields and typed strings use literal `-F` matching in BOTH audits,
and their COVERED counts are identical across runs (24 config, 4 typed) —
so the whole delta in those two rows is genuinely new shipped surface.

## Direction 1: SPEC → TREE (`spec-orphan`)

Census: 187 unique backtick-quoted terms (`proof/spec-terms.txt`), scanned
word-bounded against `src/` and `docs/map/` (`proof/spec-orphan-wordbound.txt`).
10 raw hits; 4 are filename cross-references (`AGENT.md`, and the v1.4/v1.5/
v1.6 amendment filenames) — scan artifacts, not spec terms. 6 real.

| id | target | verdict | note | disposition |
|---|---|---|---|---|
| SD1 | `ContextRequest` | spec-orphan | code has `ContextRequestV1`; STILL OPEN from 2026-08-13 P6 | parked |
| SD2 | `codec:json` | spec-orphan | STILL OPEN from 2026-08-13 P7 | parked |
| SD3 | `novel-case` | spec-orphan | STILL OPEN from 2026-08-13 P8 | parked |
| SD4 | `workflow-resume-decision.v1` | spec-orphan | 3-way spelling drift; STILL OPEN from 2026-08-13 P9 | parked |
| SD5 | `R_t` (Pareto-axis notation) | covered | code identifier is `reach` | baseline |
| SD6 | `deepreason.config.load` | covered | unqualified `load()` exists; dotted path is not a literal | baseline |

**Delta against 2026-08-13: the four parked spec-orphans (P6–P9) were never
executed and are unchanged.** The prior audit's seventh row,
`positions.accepted`, now resolves literally and is no longer raised; it was
rowed `covered` then too, so nothing moved epistemically.

## Direction 2: TREE → SPEC (`spec-silent`)

| id | surface | this audit | 2026-08-13 | delta | disposition |
|---|---|---|---|---|---|
| SD7 | CLI flags | 34 / 76 silent | 34 / 75 | +1 flag, covered — silence unchanged | parked |
| SD8 | config fields | 65 / 89 silent | 51 / 75 | **+14 fields, all silent** | parked |
| SD9 | typed error/refusal strings | 144 / 148 silent | 118 / 122 | **+26 strings, all silent** | parked |

Totals: **243 of 313 shipped surface items (78%) are spec-silent**, against
203 of 272 (75%) at the last audit. The covered counts did not move at all
(42 flags by stem, 24 config fields, 4 typed strings), so every one of the
40 new surface items shipped without a spec amendment.

Proofs: `proof/tree-cli-flags.txt`, `proof/tree-config-fields.txt`,
`proof/tree-error-strings.txt`, each with a matching `-silent.txt`.

**Count line: 6 real spec-orphan findings (4 parked, 2 baseline);
243 spec-silent items batched into 3 parked rows.**
