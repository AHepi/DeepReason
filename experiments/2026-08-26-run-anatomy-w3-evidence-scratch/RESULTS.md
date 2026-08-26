# Results — Run anatomy, tranche W3: evidence and scratch, used versus carried

Dated, honest-ledger segments. What the record shows, then the residue —
what remains unproven. Accepted does not mean true, and for a census
"measured" does not mean "explained".

---

## 2026-08-26 — the two censuses

**Scope kept.** `git diff --stat origin/main -- src/ tests/` is empty. Two
instruments, two tables, one exemplar file, all under this tranche's
directory. Every defect found is PARKED, none fixed.

**What was measured.** 64 committed run roots under `experiments/`. 28
carry citation events; 41 carry scratch events. P-R1
(`experiments/2026-08-25-poietics-program/run`, run id
`1b31f0065687bd24f64bb08acae1245446b4b31c31b90b141ff95cd5759c9a97`) is the
priority root for census (1) and is the ONLY root in the whole record whose
evidence exposure runs through the citable legend.

**Instrument agreement, first.** `evidence_census.py` is written
independently of the committed `milestone_census.py` and reproduces its
figure exactly: **212 verified citations** for P-R1, 210 conjecture-side,
2 critic-side. P-R1's registered milestone M2 stands unchanged. Everything
below is about what those 212 citations could have been, not whether they
were counted correctly.

---

### Census (1) — evidence usage

**F1. 591 of 623 admitted blocks were never shown to any model, so they
could not be cited.** `evidence/render.py::citable_legend` caps the citable
list at `maximum_blocks=32`. P-R1's dossier admitted 623 blocks over 12
documents; 32 were ever rendered into a pack, 24 of those were cited. The
591 that were never rendered are 902,387 bytes of admitted, digested,
frozen text — 93 percent of the dossier by bytes. A citation naming one of
them would have returned `EVIDENCE_REF_NOT_EXPOSED`; two such refusals are
in fact recorded. **Nothing in the record discloses that the truncation
happened.** Six of the twelve bound documents (`README.md`, `engine.json`,
`metrics.json`, `mutations.json`, `review_ledger.json`, `tests.json`) drew
zero verified citations; **three of those six** (`README.md`,
`review_ledger.json`, `tests.json`) had blocks in the legend and were passed
over, and the other three never reached it at all.

**F2. Every verified quote in P-R1 lands inside the legend's 160-character
excerpt.** The legend renders each block as an `excerpt_chars=160` preview;
`check_candidate_citations` verifies the claimed quote against the block's
FULL canonical text. Of 70 verified quotes: minimum end position 44, median
133, **maximum exactly 160, none beyond**. The byte-checking is real and the
quotes are true; what they are true OF is the preview. The clearest single
case (EXEMPLARS.md E1) quotes a section heading verbatim — the first thing
an excerpt carries.

The comparison root shows this is the regime and not the model. The record
holds two exposure regimes, and they are not comparable:

- `citable-legend` — 1 root (P-R1). ≤32 blocks, 160-char excerpts, `EVD_`
  aliases, exposure gate live.
- `dossier-pack-only` — 27 roots. Source text rendered under `SRC_` aliases,
  no exposure gate computed.

The one root with quotes reaching past 160 characters
(`2026-08-02-stress-triplet/home-triage`, reaching 1083) is a
`dossier-pack-only` root.

**F3. Citation quality: naming a handle is the commonest form, and the
record cannot tell it from a quotation.** Of 294 evidence refs recovered
from P-R1's raw responses: **146 named a block and quoted nothing**, 57
resolved to no single admitted block, 42 were quoted and byte-true, 28 were
true only after folding whitespace, 21 quoted text that is not in the block.
A bare handle still returns `EVIDENCE_CITATION_VERIFIED` — the code means
the handle resolved to an exposed, admitted, evidence-tier block, not that
any text was checked. **The typed `Measure` event carries the outcome code
and NOT the `quoted` flag**, so this split is recoverable only from the raw
response blob. That is a gap in the record's self-sufficiency, not a defect
in the check.

**F4. Citing correlates with NOT surviving. Correlation only.** P-R1's 162
conjecturer artifacts: 133 cited at least one verified block and 37 survived
(27.8%); 29 cited nothing and 21 survived (72.4%). The two groups are not
randomised — they differ in cycle, problem, seat and content, and the run
chooses what to criticise. **No causal claim is made or supported.** The
plainest confound is visible in the same census: every cycle that worked the
seed question cited the dossier (31–46 citations each), and 6 of the 7
cycles that worked a spawned `disc:`/`conn:` problem cited nothing at all.
Citing and problem-kind are entangled.

**F5. The critic's 2-of-212 is confirmed, and what it cited instead is now
visible.** P-R1 residue R3 said 2 of 212 citations were critic-side. Exact:
**3 typed `premise-citation:` Measure events, 2 verified.** The critic was
shown the citable legend 21 times (21 `citable` pack plans routed to
`argumentative_critic`), so this is not a case of the evidence being
withheld. In its raw responses the critic claimed **45** evidence refs: 21
pointed at an ARTIFACT in the run, 21 at an id resolving to neither artifact
nor block, and 3 at a dossier block. In the artifact cases the `quote` field
carries the candidate's own prose. The critic's citation behaviour is
directed at the thing it is attacking, not at the record it was given.

**F6. Attempt-4 has no attached evidence, and was cited anyway.**
`experiments/2026-08-22-change-epoch3-second-lineage/run` carries a v1
dossier reading `"acquisition_method": "no attached evidence"`, 0 sources,
0 blocks. Eight citation checks were recorded against it — 7 conjecture-side,
1 critic-side — every one `EVIDENCE_REF_UNKNOWN_BLOCK`. The harness refused
correctly; the models produced citation-shaped refs with nothing to cite.

Fourteen roots in total have zero dossier sources and non-zero citation
attempts, and the refusal code separates two cases cleanly: `EVIDENCE_REFS_
UNBOUND` where no dossier is bound at all (10 roots), and
`EVIDENCE_REF_UNKNOWN_BLOCK` where an EMPTY dossier is bound and the ref
matches nothing in it (4 roots, attempt-4 among them). Thirteen of the
fourteen recorded no verified citation whatsoever. The exception,
`live_research_2026-07-29/referee/run-d17935a4`, verified 5 — against blocks
consumed by the RESEARCH capability, which `check_candidate_citations`
admits via `extra_blocks` and which are not attached evidence. There is
therefore no attached-evidence census to run on attempt-4, and this is the
finding in its place.

---

### Census (2) — scratch usage

**F7. Writing scratch and reading it back are gated by different flags, and
P-R1 has one on and the other off.** P-R1's manifest carries
`control_plane_policy.scratch_authoring.enabled = true` and
`scratch_policy.enabled = false`. Seventeen notes were authored (14 blocks,
3 links, all by `conjecturer/deepseek-v4-pro:0813/seat0`, in cycles 3, 6 and
10). **No retrieval object of any kind exists in the root** — no
`scratch-advisory-context`, no `scratch-attention-receipt`, no pack plan
carrying a scratch item. Nothing could have read them. Eight roots are in
this state, and they are the eight most recent scratch-bearing roots
(2026-08-12 onward).

**F8. Where retrieval IS enabled, notes demonstrably reach later artifacts —
at roughly four times the rate seen where retrieval is impossible.** The
retrieval-disabled roots are a negative control the record supplies for
free: their notes provably could not be read back, so their measured reuse
rate IS the test's false-positive rate.

| group | roots | notes | notes whose distinctive wording reappears later | rate |
|---|---:|---:|---:|---:|
| retrieval enabled | 32 | 199 | 36 | **18.1%** |
| retrieval disabled (control) | 8 | 115 | 5 | **4.3%** |

Fisher exact, two-sided: **p = 0.0004**. The groups are matched on note
length (median 335 vs 319 characters) and the control group carries MORE
distinctive wording per note (66.6 vs 54.8 novel 8-word sequences), so any
length bias runs against the effect rather than for it.

"Distinctive wording" is deliberately strict: an 8-word verbatim sequence
absent from every artifact written before the note, from the problem
statements, and from every admitted evidence block. A raw overlap count
would have been worthless — a note and a later candidate come from the same
model over overlapping prompt context, and P-R1, with retrieval provably
off, still shows raw overlap on 4 of its 17 notes.

**F9. Verdicts across the 41 scratch-bearing roots.** 22 USED, 9
SERVED-BUT-NO-ATTRIBUTABLE-TRACE, 9 NOT-CONSULTED, 1 UNDECIDABLE
(`jolt_architecture_2026-07-16`, manifest schema v3, unreadable by this
version's reader — operator law 2026-08-14, reported rather than dropped).

**F10. What triggered a scratch call, and why.** A `Scratch` event is two
different things and counting them together answers nothing: some author a
note, some record that the scratchpad was READ. In P-R1 all 17 are writes,
arriving in bursts whose first event is always preceded by a `Conj` event —
the conjecturer's own turn, never criticism, consistent with
`DR-SEAM-rules-x-scratch` ("criticism receives none of it, structurally").
In `home-triage` the bursts are preceded by `Control` 9 times and `Conj` 3
times, and both seats touch the pad. The typed purpose fields are well
populated: across P-R1's 17 notes, 10 carry `why_keep_this`, 10 are marked
`unfinished`, 5 carry `possible_next_move`, and the 3 links carry
`relation_hint`/`from`/`to`.

**F11. Render-receipt cost.** P-R1 spent **zero** bytes rendering scratch —
there were no scratch packs. `home-triage` spent 477,291 rendered bytes
across 15 pack plans carrying 123 scratch items. That figure is the WHOLE
pack's rendered size for every plan carrying at least one scratch item, so
for the 6 `combined` plans it overstates what scratch alone cost; the 9
pure-`scratch` plans do not have that problem. For comparison, P-R1's
citable evidence packs cost 350,754 rendered bytes across 45 plans, and its
`plan_kind="dossier"` packs — which carry the run's own artifacts, not the
attached documents — cost 5,782,827.

---

## Residue — what this tranche does NOT establish

**R1 — internal model attention is invisible, and no instrument here can
see it.** Everything above is RECORD-LEVEL use. Whether a model read,
weighed, or was influenced by a document section or a scratch note it was
shown is not written anywhere in `log.jsonl`, `objects/`, or any blob, and
is never inferred here. A "NOT-CONSULTED" verdict means nothing in the
record served the note back; a "SERVED-BUT-NO-ATTRIBUTABLE-TRACE" verdict
means it was served and left no verbatim fingerprint. Neither is a statement
about what the model did with it.

**R2 — the 8-word shingle test catches verbatim reuse and nothing else.**
Paraphrase, adoption of a note's direction without its wording, and a note
that talked a model OUT of a line of attack are all invisible to it. F8's
18.1% is a floor on textual influence, not an estimate of influence.

**R3 — the retrieval-disabled control is 8 roots and is confounded with
date, model and configuration.** Every disabled root postdates 2026-08-12.
The contrast is the best the committed record affords; it is not a
randomised comparison, and a run deliberately configured both ways on the
same question would be worth more than all of it.

**R4 — the control's residual 4.3% is partly explained, and I did not chase
it.** At least one of P-R1's 5 control-group hits is a note that copies a
dossier excerpt the model had just been shown ("The three survivors are one
bug in two costumes…"), which my ambient filter missed because the admitted
text spells it "BEHAVIOUR" and the note spells it "behavior". The control
rate is therefore an over-estimate of the false-positive rate, which makes
F8's contrast conservative — but I have not audited all five.

**R5 — F1 and F2 are measured on ONE root.** P-R1 is the only
citable-legend root in the record. The 32-block cap and the 160-character
excerpt are read from `evidence/render.py` defaults, and no root exercises
them differently. A second citable-legend run with a dossier under 32 blocks
would separate "the cap bound here" from "the cap always binds".

**R6 — F4's survival correlation is not adjusted for anything.** Problem
kind, cycle and seat are entangled with citing, and the census reports the
raw split only. Nobody should quote 27.8% against 72.4% as an effect of
citing.

**R7 — F7's mechanism is code-reading, not record.** The RECORD shows:
retrieval policy disabled, authoring policy enabled, 17 notes written, no
retrieval object. The explanation offered in PARKED.md P4-W3-2 —
that `rules/conj.py`'s v6 authoring path validates against
`control.scratch_authoring` alone while `authoring.py::_validate_v6_authority`
also requires `scratch_policy.enabled` — comes from reading the source and
carries the weaker authority of the two. It is a hypothesis for the parked
tranche to reproduce, not a finding.

**R8 — no root sweep, and none owed.** The root sweep is retired as an
instrument (operator ruling 2026-08-22). Both censuses read committed roots
read-only and assert nothing about their verdicts.

**R9 — a map document this census needed does not exist.** `SUB-evidence`
declares `Seams:` empty and lists `evidence x rules` as undocumented. That
is precisely the seam measured here — where `rules/conj.py` files
`evidence-citation:` and `rules/crit.py` files `premise-citation:`. Parked
as P4-W3-4; not authored in a read-only tranche.
