# SPEC — provenance history as a seat-queryable channel

**STATUS: DRAFT. Sections marked `[PENDING M#]` are not final and must not be
implemented from.** Every such section is blocked on a measurement that was
pre-registered in `PREREG.md` before the arms launched. Phase 1 ends when the
M-results land, those sections close, and the operator approves this document
and `CHECKLIST.md` (C8). No production code is written in this phase.

Authority: `REQUEST.md` R1–R15, C1–C15, G1. Every item below traces to a
requirement number and, where the window instruction requires it, to an
M-result.

---

## 0. What is being specified, in one paragraph

A conjecturer or critic seat can ask a bounded, typed question about how an
artifact came to be — what it descends from, what was tried against it, what
was discharged — and receive a bounded answer that is recorded as an exposure
receipt. The vocabulary of questions is CLOSED and VERSIONED. The sources it
can draw on are a REGISTRY of channels, one of which is mini's episode log.
Which seat may see which channel is per-run CONFIGURATION with typed
disclosure when a channel is off. Nothing here lets a model author a query
that becomes code.

---

## 1. Two things the record already settled, before any design

Both were verified at base rather than assumed, and they bound the design more
than anything in the request does.

**1.1 Conjecturers can already ask; critics cannot ask at all.** The
context-expansion path exists for conjectures — `max_context_expansion_requests`
(`run_manifest.py:576`), the request/denial/grant machinery in `rules/conj.py`
(344, 2360, 2373, 2950), the typed denials `channel_not_permitted`,
`capability_not_granted`, `request_limit_reached`. `rules/crit.py` contains
**zero** occurrences of `context_policy`, `desired_retrieval_channels` or
`context_expansion`. So R3's "another conjecturer **or critic** could search
through" is half-buildable on the existing path and half not. This is the
single largest scoping fact in the tranche and §4 is shaped by it.

**1.2 The obvious implementation is the expensive one.** Reusing
`RetrievalChannel` and adding provenance members to `_ATTENTION_CHANNELS`
(Road A) was priced, not argued (`PRICE_CHANNEL_WIDENING.txt`,
`BLAST_RADIUS.txt`):

| | measured |
|---|---|
| P1 qualification subject digest | MOVES, `02ee7e09…` → `059b3e0d…` |
| P2 committed manifests still valid | **0 of 69** — `channel_priority` must contain EVERY channel in frozen order and `per_channel_limits` must name EVERY channel, so an older manifest is broken rather than merely narrower |
| P3 `direct_open` refusals | keyed to that MEMBER, not to the attention list |
| P4 a non-attention channel in `permitted_retrieval_channels` | **rejected by the validator** — so it could never be granted, only denied `channel_not_permitted` forever |
| `tools/blast_radius.py` | `frozen_surface_verdict: CONTACT`, `DIRECT` on `run_manifest.py`, `qualification_digest: CONFIRMED` |

P4 is the decisive one: Road B cannot piggy-back on `RetrievalChannel` either,
because a channel outside `_ATTENTION_CHANNELS` can never enter the permitted
list. The provenance vocabulary therefore needs its own request field and its
own permitted list regardless — more code, zero frozen contact.

**Road chosen: B — a declared interface of its own.** Decided without asking,
as dominant under the operator's modularity law of 2026-08-26 ("when a design
forks between a tighter coupling that is smaller and a declared interface that
is larger, the interface wins"). Recorded in the Phase 1 evidence commit;
override any time.

---

## 2. The closed query vocabulary (R3, R4, R5)

**S1 — queries are a closed, versioned enum, never a string.** A seat names a
query by KIND plus typed arguments. There is no free-text query, no expression
to parse, and nothing a model writes is ever evaluated. That is not caution
for its own sake: a model-authored query that becomes executable is the shape
CLAUDE.md's treadle section forbids outright, and it is the difference between
a query surface and arbitrary code execution wearing a work item's clothes.

`provenance.query.v1`, the initial closed set:

| kind | argument | answers | bound |
|---|---|---|---|
| `lineage` | artifact ref | what this artifact was revised from, and what from that | ≤ 8 ancestors |
| `attacks` | artifact ref | objections raised against it, each with landed/not-landed — **the not-landed half needs a source that is NOT `att`; see PARKED P7** | ≤ 12 edges |
| `discharges` | artifact ref | objections answered, with the discharge | ≤ 12 |
| `verdict_history` | artifact ref | status transitions in order, with the warrant that caused each | ≤ 16 transitions |
| `siblings` | problem ref | other candidates proposed for the same problem | ≤ 12 claims |
| `commitment_origin` | artifact ref | how this artifact's commitment battery was arrived at — R4's own words, resolved in §2.1 | ≤ 12 commitments |
| `episode_pool` | work ref | the mini episode pool this call's candidates were built from (R2) | ≤ 24 pool lines |

**S2 — every answer is bounded twice.** Once by the per-kind row cap above,
and once by a character cap charged against the pack budget (§5). A query that
would exceed either is truncated with the truncation STATED in the answer text.
Silent truncation is forbidden: an answer that dropped its tail invisibly
would make every result built on it unfalsifiable.

**S3 — answers are deterministic and replayable.** The same query against the
same record yields the same bytes. No embedder, no ranking, no sampling in the
answer path; ordering is by the record's own sequence.

### 2.1 Two terms of the operator's resolved from the record, not invented

**"commitment battery" (R4)** is `artifact.interface.commitments` — the
operator's own prior vocabulary, used on 2026-08-22 ("an artifact carrying an
EMPTY own commitment battery may NOT ground reach") and resolved narrowly in
that tranche to exactly this field. `Interface` lives at
`ontology/artifact.py:31` and carries `commitments: list[str]` plus `refs`.

**"commitment interface" (R5)** is that same `Interface` — the structure a
conjecturer fills in when it proposes an artifact. So R5 is precise rather than
loose: a conjecturer filling in `Interface.commitments` after a mini run
benefits from seeing how earlier artifacts' batteries were arrived at, which is
exactly `commitment_origin`. Q2 and Q3 in `REQUEST.md` are hereby answered from
the record; neither needed the operator.

---

## 3. The channel registry (R1, R2, C2, C3)

**S4 — channels are a versioned registry on the P9 plugin shape.** The
operator's law (C2) is that "the scratch pad option must function like a plugin
that allows for movement elsewhere as well". The repo already has one worked
instance of exactly this shape, and it is copied rather than reinvented:
`successor/registry.py` + `route.py`, resolved lazily through a declared hook
in `aftercycle.py`, with `config.py` owning the default destination id, and a
law-line test that forbids every DECIDING package from naming the machinery
with an EMPTY permitted-exception list.

Registered channels at v1:

| channel | source | kind |
|---|---|---|
| `record.lineage` | the run's own log and state | record-derived |
| `record.attacks` | attack edges + warrants | record-derived |
| `record.discharges` | the discharge channel | record-derived |
| `record.commitments` | artifact interfaces | record-derived |
| `episode.pool` | mini's episode log (R2) | registered scratch destination |

**S5 — `episode.pool` is a REGISTERED DESTINATION, not a special case.** R2's
"Mini produces its own log" is served by registering that log as one channel
among several, so it is re-aimable by configuration and so history works
identically with episodes on or off (monitor's reading point 5). Its current
shape on the model-profile branch is a JSONL trace "self-metered outside the
harness's accounting" (`CONFIG.md`); whether v1 reads that shape or requires
the pool to become a first-class record object is `REQUEST.md` Q6 and is
resolved in §7, because it is the one place a new record kind could be forced.

**S6 — a channel that cannot answer COMPILES.** Per the all-configurations law
(C5) and the signal-contract pattern, a topology with no episode log does not
fail; the query returns a typed "channel unavailable" answer and the run
records the notice. Disclose, never die.

---

## 4. The per-seat exposure policy (R3, R6, R7, C1, C5, C6)

**S7 — exposure is keyed by SEAT INSTANCE, not by role.** The signal-contract
law is explicit that one conjecturer may sit in "multiple structurally
asymmetric seats that may need throttling independently", so the policy key is
the seat instance, matching `cap:<role>#<seat>` which `invariants.py` already
resolves.

**S8 — every gate is switchable per run, and switching one off emits a typed
WARNING, never a refusal and never silence.** This is C1 verbatim ("Gates are
always optional: with warnings"). It is also the law that audit finding P10
violated twice over — five switches silently reverted by the manifest echo with
zero notices — so the acceptance check for S8 is that turning a channel off
produces a notice a reader can find in the record, not merely that the channel
is off.

**S9 — the policy is CONFIGURATION, recorded, under grant G1.** Two `Config`
fields, popped in `_versioned_source_config_data` so they never enter
`engine_config_json`. Measured before the grant was requested
(`PRICE_EXPOSURE_POLICY.txt`): without the pop, `source_config_hash` moves at
**all six** schema versions; with it, byte-identical at every version. Grant G1
covers this SHAPE; field names and count are fixed in `CHECKLIST.md`, and any
departure from insertions-only or from digest preservation is a fresh stop.

**S10 — DEFAULTS. `[PENDING M1, M3]`** The conjecturer default and the critic
default are decided by the measurements, by the table pre-registered in
`PREREG.md` §3 before any arm ran, and not by whoever reads the numbers:

| M3 outcome | critic default |
|---|---|
| C1 sharpness clearly lower | BLIND |
| C1 sharpness clearly higher AND re-raise rate lower | INFORMED |
| anything else, including a split | BLIND, and it goes to the operator as a stop (C13) |

Blind remains available as a default in every branch regardless of outcome
(monitor's reading point 3), because R7 is the operator's own hypothesis and
the shipped behaviour.

**S11 — critics get an ask path or they do not get one.** Per §1.1 a critic
cannot request anything today. If M3 says INFORMED, this spec must either build
the critic-side request path or specify harness-side exposure without a
request; if M3 says BLIND, neither is built in Phase 2 and the channel exists
for conjecturers only. `[PENDING M3]`

---

## 5. Recording and bounding (R3, C7)

**S12 — a query result is recorded as an exposure receipt, reusing
`ContextExposureReceiptV2`.** The shape already exists
(`workflow/transaction.py:270`, registered as `workflow-context-exposure-v2` at
`harness.py:1071`, `storage/objects.py:167`, `workflow/replay.py:86`) and
already carries `prompt_sha256`, `context_plan_refs` and `exposed_items` with
uniqueness validators. Reusing it is what keeps §7's frozen forecast at zero.

**S13 — answers are charged against the pack budget, and the budget is smaller
than it looks.** Measured over 532 committed prompts (`SCHEMA_SHARE.txt`):

| contract | prompt chars | schema chars | share |
|---|---|---|---|
| `conjecturer.turn.v6` | 19,976–26,867 | 16,141–18,951 | **60.0–81.4%** |
| `conjecturer.atomic-candidate.v1` | 11,179 | 6,154 | 55.1% |
| `batch-critic.v2` | 3,055–5,726 | flat 1,275 | 27.0–42.2% |
| `critic.atomic-target.v1` | 3,287–5,794 | flat 1,253 | 21.7–38.2% |

P-A1's "~19k of 30k chars" is confirmed almost exactly on pc2-rematch (18,951
of 26,214). Consequences that bind this spec:

1. a provenance answer competes only for the NON-schema remainder — roughly
   5,000–11,000 chars on a conjecturer call, not the whole prompt;
2. the per-seat asymmetry is a measurement, not an opinion: a critic's schema
   is a flat ~1.3k against a conjecturer's ~16–19k, so a **critic pack has far
   more unspent room for history than a conjecturer pack does** — the opposite
   of where R6 and R7 point. §4's defaults are set by M1/M3, but this is the
   cost side of that decision and it is recorded here.

**S14 — the schema-every-call cost is a FINDING, not a fix.** The window
instruction is explicit that it is out of scope here. Recorded so the next
tranche has it: the largest single lever on conjecturer prompt size is not the
pack budget at all.

---

## 6. The anti-attractor shaping rule (R8) `[PENDING M1]`

**CORRECTION, from PARKED P7, before any of this is implemented.** The rule's
second limb — failed attacks — cannot be built from `att`. A not-landed attack
mints no warrant and therefore materializes no edge, so `att` holds only
attacks that landed; sustain rate is 1.000 across 6 committed roots and 630+
targets. The limb must be sourced from criticism records that did not warrant
anything, or dropped and said to be dropped. M1's treatment arm ran with this
limb empty, so the hypothesis was tested at half strength — and the missing
half is the one R8 most directly names.

**S15 — exposure is SHAPED, not complete.** Refuted lineages and failed attacks
are shown; the winning lineage is shown only on explicit request. The
hypothesis is that showing what has already died is anti-attractor information
while showing the winner is the attractor itself. This is registered in
`PREREG.md` §1 as M1's primary falsifiable prediction — H1 lowers the
near-duplicate rate — and the render that tests it withholds the winner by
construction (`render_history.py`).

**If M1 shows H1 RAISES the near-duplicate rate, S15 is wrong as specified and
may not be adopted.** That is a C13 stop, not an adjustable parameter.

---

## 7. Frozen surfaces — forecast here, not discovered later (C7)

| surface | forecast | disposition |
|---|---|---|
| 3 — `invariants.py` / `verification/` | contact **only if** a new typed event or object kind must be recognised by replay validation | **AVOIDED.** S12 reuses `ContextExposureReceiptV2`, which replay already recognises. No new record kind, no `_EPISTEMIC_CHECKS` entry, no `report.py` channel. If §5's design ever requires one, that is a PRICED STOP before any code. |
| 4 — `run_manifest.py` | contact **if** the exposure policy is stamped into the manifest | **GRANTED (G1), and priced first.** Two `Config` fields + two `data.pop` lines. E1/E2 measured: hash moves at all six versions without the pop, byte-identical with it. Insertions-only, digest-preserving, on the recipe granted twice before. |
| 4 — `_ATTENTION_CHANNELS` | contact if Road A were taken | **NOT TAKEN.** Road B is chosen; §1.2 carries the price that decided it. |
| 1, 2, 5 — `capabilities/state.py`, `harness.py`, `qualification.py` | none expected | none. |
| frozen-adjacent `route_fingerprint` | none expected | none. |

Committed roots stay read-only throughout. `render_history.py` opens every root
with `read_only=True`, because a writable open repairs — that is, destroys —
the evidence.

---

## 8. The episode switch (R10, R11, C9)

**S16 — "episode config" is CONFIGURATION, not the environment variables on the
experiment branch.** The operator named it (R10: "Mark this new configuration
down as 'episode config'. An episode runs in each mini run") and fixed mini's
role (R11: generator, thinking off). C9 forbids merging that branch, so this
spec does not import its code; it specifies the switch and leaves the generator
itself to the phase that lands it. History works with episodes on or off (S6,
monitor's reading point 5), which is why the two are separable at all.

---

## 9. Acceptance checks

One per specification item, each falsifiable. `[PENDING]` rows close when their
measurement lands.

| item | acceptance check |
|---|---|
| S1 | a query naming a kind outside the closed enum is refused typed; no code path evaluates model-authored text |
| S2 | an over-long answer is truncated AND the truncation is stated in the answer text — asserted by a test that mutates the cap |
| S3 | the same query twice over one root yields byte-identical answers |
| S4 | a law-line test: no deciding package names the registry; the permitted-exception list is empty |
| S5 | `episode.pool` resolves through the registry with no caller naming it |
| S6 | a topology with no episode log compiles and records the typed notice |
| S7 | two seats of the same role carry independent policies |
| S8 | switching a channel off emits a findable typed notice — not merely off |
| S9 | `source_config_hash` byte-identical at all six schema versions; the fields never reach `engine_config_json` |
| S10 | `[PENDING M1, M3]` |
| S11 | `[PENDING M3]` |
| S12 | a query result appears as a `workflow-context-exposure-v2` receipt; `verify_root` green; no new object kind |
| S13 | an answer that would exceed the remaining pack budget is bounded before render |
| S15 | `[PENDING M1]` |
| S16 | the episode switch is reachable as configuration with no code edit |

---

## 10. Open items carried into CHECKLIST.md

- Q6 (`REQUEST.md`): whether `episode.pool` v1 reads the JSONL trace shape or
  requires a first-class record object. §7 depends on the answer staying on the
  read-a-trace side; if it does not, that is a surface-3 priced stop.
- Q4: this spec specifies the ASK (a seat requests; §2), while M1/M3 test the
  PUSH (a section rendered into the pack unasked). They are not the same
  mechanism, and `PREREG.md` residue #2 says so: a positive M1 licenses
  "history content helps", never "the query surface works".
- The map has no `CON-provenance` and no `SEAM-rules-x-verification`. Writing
  the covering document is part of Phase 2, in the same commit as the code.
