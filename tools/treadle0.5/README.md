# treadle 0.5.0

A method library for LLM-assisted formal work: skills (PROMPT-CORE discipline
blocks an agent reads before acting), checkers (single-file stdlib tools whose
exit codes are the only acceptance), and the glue rules that bind them.

**Start at `SETUP.md`.** It is written for the LLM doing the installing.

## Lineage, stated honestly

0.5.0 is rebuilt from the subset of treadle 0.4.1 that was installed and
field-tested in one long working cycle on the Poietics repository, plus the
instruments that cycle invented. The 0.4.1 archive itself is gone; modules
that were never installed (M1 swarm gate, the M2 driver's board and stage
table) are **not carried** — `MODULES.md` records what replaced them and what
to do if their job returns.

Everything that IS here earned its place the hard way: `FIELD_REPORTS.md`
lists thirteen numbered defects observed in that cycle — an author reversing a
recommendation under review, a false claim propagating across documents, a
reviewer returning nothing because its packet was too big, a determinism test
that could not see the nondeterminism it guarded against — and maps each to
the module or rule that now prevents it. The library's own tooling was
hardened against field reports 10–13 in 0.4.x; 0.5.0 continues the numbering.

## What changed from 0.4.1, in one table

| change | driven by |
|---|---|
| Four new skills: `decision-mapping`, `expressibility-probe`, `precedent-transport`, `review-response` | FR-21..FR-24 |
| Disposition typing (DECIDE / PROPOSE / ESCALATE) added to `term-pinning` | FR-21 |
| Option-level discrimination check added to `denotation-tests` | FR-20 |
| Refutation modes (COLLAPSE / SPLIT) and separability statement added to `example-battery` and `FORMAT.md` | FR-20 |
| "No count from memory" added to `mapping-table` | FR-26 |
| Run-versus-read rule added to `discharge-typing` | FR-25 |
| Reviewer packet rule added to `semantic-round-trip` | FR-15 |
| New checker `consistency_packet.py` — cross-document claim agreement | FR-14 |
| New checker `influence_probe.py` — measured read surfaces, not argued ones | FR-25 |
| New checker `review_harness.py` — packet governor, hash-chained ledger, superseded-row semantics, provenance-not-reproducibility | FR-15..FR-17 |
| `selftest.py` — every guard proven against a planted violation before use | FR-18 |
| M2 driver retired in favour of the `review-response` loop | see MODULES.md |

## Acceptance

```sh
python3 treadle0.5/selftest.py
```

Deterministic, offline, stdlib-only. It does not merely run the checkers on
good input: for every guard it also plants a violation and requires the guard
to FAIL. A guard that cannot be shown to fail is treated as not existing —
that rule is FR-18, and three guards in the source cycle were vacuous until it
was applied.

## The one-sentence philosophy

Never a model judging doneness; never a claim about code that was not run;
never a recommendation wearing a finding's clothes; and every guard proven
guilty of working before it is trusted.
