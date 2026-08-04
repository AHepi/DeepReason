# Request: rung 4 — every run records which modules built it
Captured: 2026-08-04. Authority is two sources, both quoted verbatim
below. Rung 3 is complete across its two tranches; this is a clean
tranche on a clean rung, per C1.

## Verbatim

> ### Rung 4 — every run records which modules built it  [EXECUTE WITH GUARDRAILS]
> Route: `dr-change-orchestrator`.
> Goal: registered modules stamp a fingerprint (the
> `CONTAINED_WORKER_SHA256` precedent in `verification/contained.py`) into
> the run's TYPED RECORD so cross-run comparisons are honest.
> GUARDRAIL (hard): the fingerprint rides Config and typed log/object
> records — NEVER a new manifest field and NEVER anything entering the
> qualification subject digest. Both are frozen (surfaces 4 and 5); a
> manifest field also invalidates every cached qualification (~14 min per
> home to rebuild). If the design cannot avoid the manifest, that design is
> DESIGN-AND-STOP: write SPEC.md, stop, present to the operator.
> Reader-before-writer: the reader must treat ABSENCE of the fingerprint
> (every existing root) as valid before the writer emits it.
> Accept: full gate; sweep byte-identical (absence-tolerant reader proven
> by the sweep itself).
>
> — `docs/HANDOVER_2026-08-03.md`, "The program: seven rungs, in order,"
> Rung 4. Re-extracted from the file this turn, not carried from memory.

> Next Rung. Read claude.md again
>
> — operator's message this session, sent immediately after my closing
> report on rung 3 tranche B. That report's final line read: "Rungs 4-7
> are untouched and remain the operator's call — per C1, a tranche that
> touched rung 3 may not begin rung 4." Per
> `dr-ask-the-right-question`'s reading table, "Next Rung" answering a
> report that named rung 3 complete and rungs 4-7 pending is
> authorization for exactly ONE rung — the next in the handover's own
> stated order, rung 4 — and for no rung beyond it. "Read claude.md
> again" was complied with before any other action this turn.

## Map preflight (resolved ids, recorded here so every later phase starts
## from the same map)

- `DR-INV-frozen-surfaces` — read IN FULL this turn. Surface 2 =
  `harness.py` event application and well-formedness; surface 4 =
  `run_manifest.py` manifest schemas AND their validators; surface 5 =
  anything altering qualification subject digests (`qualification.py`).
  Its "Where authority is allowed to live instead" section is the
  `Config` precedent the guardrail invokes; its final `Traps` entry is
  the one Q1 turns on.
- `DR-SEAM-harness-x-verification` — read IN FULL this turn, BEFORE
  either subsystem it joins, per the map's one ordering rule.
  `Owns: harness.py, invariants.py, log/event_log.py, storage/blobs.py`.
  Its "How to change it" steps 2, 3 and 6 bind this rung's design
  directly (see Q3, Q4, C7).
- `DR-SUB-verification` — owns `verification/contained.py`, home of the
  precedent the rung names. Verified fresh this turn:
  `contained.py:354` is
  `CONTAINED_WORKER_SHA256 = sha256_hex(CONTAINED_WORKER_SOURCE_V1.encode("utf-8"))`
  and `contained.py:493` emits `"worker_sha256": CONTAINED_WORKER_SHA256,`
  inside a fingerprint dict. `SUB-verification.md:115-117` already
  carries a check pinning both lines.
- `DR-SUB-harness` — frozen (surface 2). "typed log/object records" is
  its territory.
- `DR-SUB-manifest` — frozen (surface 4). The guardrail's hard NO.
- `DR-CON-schools` / `DR-SEAM-schools-x-scheduler` — rung 3's
  `SCHOOL_POPULATION` registry. The most likely, but UNVERIFIED,
  referent of "registered modules" (Q2).

## Requirements

R1 (process): "Route: `dr-change-orchestrator`."

R2 (behavior): "registered modules stamp a fingerprint ... into the
run's TYPED RECORD so cross-run comparisons are honest."

R3 (process/design): "(the `CONTAINED_WORKER_SHA256` precedent in
`verification/contained.py`)" — the named shape to copy, exactly as
rung 3 was told to copy `verification/registry.py`.

R4 (behavior/constraint): "the fingerprint rides Config and typed
log/object records".

R5 (constraint): "NEVER a new manifest field" — "Both are frozen
(surfaces 4 and 5); a manifest field also invalidates every cached
qualification (~14 min per home to rebuild)."

R6 (constraint): "NEVER anything entering the qualification subject
digest."

R7 (process): "If the design cannot avoid the manifest, that design is
DESIGN-AND-STOP: write SPEC.md, stop, present to the operator."

R8 (process/behavior): "Reader-before-writer: the reader must treat
ABSENCE of the fingerprint (every existing root) as valid before the
writer emits it."

R9 (process): "Accept: full gate".

R10 (process): "sweep byte-identical (absence-tolerant reader proven by
the sweep itself)."

R11 (process): "Next Rung" — authorization to open exactly one rung,
the next in the handover's stated order, and nothing beyond it.

## Standing constraints

C1: "One rung per tranche, minimum. A rung may take several tranches;
never let one tranche touch two rungs. Never begin rung N+1 in a tranche
that touched rung N." — `docs/HANDOVER_2026-08-03.md`, "Executor
calibration." This tranche is rung 4 only; rungs 5-7 remain untouched.

C2: "Every rung ends with: acceptance commands run and pasted, tranche
committed and pushed, PARKED.md holding everything you noticed but did
not do." — same source.

C3: "Do not write to `docs/ERRATA_EXECUTOR.md` (operator-directed,
2026-08-03, superseding this file's earlier feed-instruction). That
ledger has ONE writer: the monitoring session. When anything in this
file or the skills misleads you, contradicts the record, or is silent
where you needed it to speak, record the observation in your own
tranche's artifacts (PARKED.md or the phase document where it
surfaced) with the evidence pointer, then resolve the question itself
via `dr-ask-the-right-question`." — same source.

C4: "The frozen surfaces (`docs/map/INV-frozen-surfaces.md`) bind every
rung: state digests, harness event application, replay-validation
formats, manifest schemas AND validators, qualification subjects.
Readers may be fixed; formats may not; a change that moves a committed
root's verdict is wrong by definition." — same source. **This rung is
the one where that constraint is load-bearing rather than incidental:
three of the five surfaces sit directly on the design's path.**

C5 (inherited, standing across this session): known flake
`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
can fail once under `-n 4`, rerun before diagnosing; commit and push at
every phase boundary; stop conditions are hard stops; where a spec is
silent, load `dr-ask-the-right-question` and route to the cheapest
authority — do not improvise; full gate must be run with `python -m
pytest`, never bare `pytest`.

C6 (NEW, this rung): the rung is tagged "[EXECUTE WITH GUARDRAILS]" and
carries three distinct constraints on HOW, each quoted verbatim in
R4-R8 above: the hard guardrail's two NEVERs (R5, R6), the
reader-before-writer ordering (R8), and the DESIGN-AND-STOP escape
hatch (R7). Unlike rungs 2 and 3, which were tagged EXECUTE, this rung's
own text anticipates that its design may be inadmissible and says what
to do about it — which makes "stop and present SPEC.md" a sanctioned
outcome here, not a failure.

C7 (NEW, from the map rather than the operator, and binding for the same
reason C4 is): `DR-SEAM-harness-x-verification`, "How to change it"
step 6 — "**If a change makes an existing root unopenable, it is wrong
by definition.** The symptom is not a helpful error: the root collapses
to a single `open` finding with empty `stats`, which erases every other
finding it would have produced." And step 3, on the ordering a new
typed event channel must move in — "Stopping before the last step
defaults the new finding to `integrity`, and `integrity` is what decides
`valid` — so every recorded root that trips it flips. See
`DR-SUB-verification`'s first trap." Both bind this rung's design
directly and are recorded here so no later phase can treat them as a
discovery.

## Open questions (for dr-spec-change)

**Q1 — the sharpest: a possible requirement-vs-record contradiction
between R4 and R5.** R4 says the fingerprint "rides Config"; R5 says
"NEVER a new manifest field". `DR-INV-frozen-surfaces`' final `Traps`
entry — written by our own rung 2 tranche 2, and itself pinned by a
check — establishes that the same document's earlier blanket claim ("A
`Config` value costs nothing to add and is invisible to replay") is
FALSE: a new top-level `Config` field DOES enter `source_config_hash` /
`engine_config_json` / the compiled manifest's `sha256` unless
`_versioned_source_config_data` in `run_manifest.py` is explicitly told
to pop it, per schema version. `run_manifest.py` IS surface 4. So R4 and
R5 may be jointly unsatisfiable without exactly the operator-approved
surface-4 touch that rung 2 tranche 2 paid for (that tranche's
REQUEST.md Amendment 3). R7 supplies a documented escape hatch whose
applicability is a spec-phase judgement, not a capture-phase one.

**Q2 — WHICH "registered modules" stamp a fingerprint.** R2's words do
not say. Verified fresh this turn, the tree has three registries:
`SCHOOL_POPULATION` (`capture/schools.py:323`, built by rung 3, exactly
one entry), `VerifierRegistry` (`verification/registry.py:30`), and
`WORKLOADS` (`workloads/registry.py:30`). Noted without deciding: rung
3's registration ALREADY pins a fingerprint at registration and
re-checks it on resolve — that was the shape rung 3 was told to copy —
so what "stamp into the run's TYPED RECORD" adds beyond what already
exists is itself part of this question.

**Q3 — WHERE in the typed record.** R4's "typed log/object records"
names two different stores: the append-only event log and the
content-addressed object store (`storage/blobs.py`, the `objects/`
directory). `DR-SEAM-harness-x-verification`'s "How to change it" step 3
states the fixed order a NEW typed event channel must move in (`Rule`
and the payload field in `ontology/event.py` → the `_apply_event` branch
→ a `_reset` attribute if it materializes state → the `record_*` seam →
a determinism finding in `verify_root` → a channel entry in
`report.py`), and `_apply_event` is frozen surface 2. Whether R2 intends
a new channel, a defaulted field on an existing record, or an
object-store write is undetermined by the rung's words, and the three
differ materially in which frozen surfaces they touch.

**Q4 — what "the absence-tolerant reader proven by the sweep itself"
(R10) requires as evidence.** R10 makes one instrument do double duty:
byte-identical AND the proof of absence-tolerance. Whether a
byte-identical sweep alone constitutes that proof, or whether a separate
reader-level assertion is also owed, is not stated. Available precedent,
noted without adopting it: `DR-SEAM-harness-x-verification`'s step 2
names `attempt_trace` as the worked reader-before-writer example —
defaulted so old events still validate, demanded only when
`manifest is not None`.

**Q5 — whether the fingerprint can avoid `Config` entirely**, computed
at emit time and written straight into a typed record, with no new
`Config` field and therefore no `run_manifest.py` touch. If buildable,
Q1's contradiction dissolves. Whether it is buildable against the real
write path is a spec-phase question to be VERIFIED, not assumed — and
note it would sit in tension with R4's literal words, which name Config
as one of the two things the fingerprint rides.

## Amendments

**Amendment 1 (2026-08-04, arrived mid-capture — not an operator message
but a correction to the authority document this tranche quotes).** While
this REQUEST.md was being written, the monitoring session pushed
`69c51928`, which edits `docs/HANDOVER_2026-08-03.md` — the source of
every R above. Verified fresh after rebasing: **rung 4's own text is
byte-identical to what is quoted above** (the diff touches only rung 3's
accept line and the environment-facts list). But two of its additions
bind this rung, so they are ledgered here BEFORE any spec work, per the
orchestrator's rule that a new instruction is appended before it is
acted on.

C8 (NEW, verbatim from the corrected handover, rung 3's block):

> Rule for the remaining rungs: accept lines state PROPERTIES; any named
> mechanism is a suggestion the spec phase must verify for reachability.

This governs rung 4 directly and changes the binding force of **R3**:
`CONTAINED_WORKER_SHA256` is a NAMED MECHANISM, so it is a suggestion
this tranche's `dr-spec-change` must verify for reachability — not a
mandate to copy. The rule was minted because rung 3's named fixture
turned out to be unreachable and the executor caught it at spec time;
R3 is the same shape of clause in the same document, and it now inherits
the same treatment. R3 is NOT superseded — the precedent may well be the
right shape — but it is demoted from binding to advisory, and Q2/Q3 must
test it rather than assume it.

C9 (NEW, verbatim from the corrected handover's environment facts):

> `docs_verify --fast` reuses cached check results, so it CANNOT catch a
> map document newly broken by a `src/` change — only the full
> `python tools/docs_verify.py` re-derives everything. Iterate with
> `--fast`; run the full mode at least once before any commit that
> touches `src/` (rung 3 evidence: the full run caught a fifth affected
> document, `SEAM-scheduler-x-rules.md`, that `--fast` had passed —
> commit `55b16ce9`; ERRATA E10).

This is rung 3 tranche B's own finding, promoted by the monitor from a
tranche artifact into a standing environment fact. It binds this
tranche's plan: any step that touches `src/` owes a FULL `docs_verify`
before its commit, not a `--fast` one.

**Amendment 2 (2026-08-04, operator message, verbatim).** Sent in
response to the capture above, before any spec work began:

> Good capture. Proceed to dr-spec-change. On Q5: verify against the real
> write path; prefer any design with zero frozen-surface contact. If every
> workable design needs the surface-4 scrub line, DESIGN-AND-STOP per the
> rung and present the options — do not assume rung 2's approval carries
> over to a new touch. C7's integrity-default trap: any new typed channel
> must land its report.py entry in the same commit, or not exist yet.

New requirements, quoting the operator's own words:

R12 (process): "Proceed to dr-spec-change."

R13 (process): "On Q5: verify against the real write path" — the
buildability of a Config-free design is to be VERIFIED against the
actual code, not reasoned about abstractly. This is the operator
converting Q5's own caveat into an obligation.

R14 (design constraint): "prefer any design with zero frozen-surface
contact." A preference ordering over designs, not a prohibition:
zero-contact designs win where one exists.

R15 (process, a stop condition): "If every workable design needs the
surface-4 scrub line, DESIGN-AND-STOP per the rung and present the
options — do not assume rung 2's approval carries over to a new touch."
Two obligations in one sentence: (a) DESIGN-AND-STOP is mandatory, not
optional, if no zero-contact design is workable; (b) rung 2 tranche 2's
operator approval for touching `run_manifest.py` is explicitly NOT
transitive to this tranche. Q1 may therefore NOT be resolved by
appealing to that precedent.

R16 (process/behavior): "C7's integrity-default trap: any new typed
channel must land its report.py entry in the same commit, or not exist
yet." This resolves the ordering half of C7 by operator instruction: a
partial channel is forbidden outright, not merely warned against. Note
it also frames the alternative plainly — "or not exist yet" sanctions
NOT building a channel at all.

(append-only; later operator messages land here as R<n+1>... or
"R2a supersedes R2", each with its verbatim quote)
