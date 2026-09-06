# Spec for: "the forms needs to change so that the conjecture seat can handle and organise the new log shaped content" — then "test on the full harness"
Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.
Tranche dir: `experiments/2026-09-06-change-writers-room-organiser-testing/` (below, `<T>`).
Room root (read-only): `experiments/2026-09-06-change-writers-room-limits-and-forms/runs/home-room/shallow-runs/shallow-0b47bc7b090854078ddf7559` (below, `<ROOM>`).

## How the room reaches the seat, measured before design (the answers to Q1–Q8)

The brief's design names mechanisms; each was traced to the code it reaches
before being adopted (dr-spec-change rule 2). Measurements M1–M12 below are
the evidence; this section states what they decide.

**The form (Q1).** The managed `deepreason reason` conjecturer dispatches
`conjecturer.turn.v6` (`rules/conj.py:2340-2353`: under `active_v6` the
contract is `configured_turn_contract`, never `reasoning.conjecturer.compact.v2`).
Its candidate on the reasoning workload IS `ReasoningCandidateProposal`
(`wire.py:1637-1644`, `ReasoningConjecturerTurnWireV4.candidates: list[ReasoningCandidateProposal]`,
inherited by V5 and V6) — claim, mechanism, counterconditions ≥1,
typicality, evidence_refs ≤8 (`workloads/text.py:142-167`) — and the
reasoning branch is taken because every public text run seeds the
`program:reasoning-envelope-wf` criterion (`text.py:301-302`, read at
`conj.py:1431-1435`). Counterconditions become commitments at
`conj.py:2142` through `draft_countercondition_commitments`. So the brief's
named form does NOT reach the managed path; the PROPERTY it names (a
commitment-bearing candidate on the existing form) does, through
`conjecturer.turn.v6`, whose candidate is the same proposal type. The
organiser shell therefore pairs `form_id="conjecturer.turn.v6"` — the form
the seat actually fills — and this contradiction is recorded (A1). C8 holds:
no new form.

**The registration road (Q2).** `load_operator_plugins` — the loader for
`<DEEPREASON_HOME>/seat_plugins/` (`.py`, `.tmpl`, `.layout.json`) — has
exactly ONE call site in `src/`, `shallow.py:71-73`, the reduced engine's
setup (M3). The managed path never opens that directory. The brief's own
fallback clause applies: the layout, the shell, the directive plugin and
the wording register in `llm/seat_layouts.py`, `llm/seat_plugins.py` and
`llm/role_prompts.py` — none frozen (M1) — and the gap is PARKED (P1).
Shell selection on the managed path is `DEEPREASON_SEAT_SHELL=conjecturer=<id>,argumentative_critic=<id>`
(`seat_sections.py:456-470`, read by `resolve_seat_shell` → the walk's
`resolve_seat_pack_layout`); wording selection is
`DEEPREASON_ROLE_PROMPT_TEMPLATE=<id>` (`roles.py:404`). Neither is `Config`,
so neither moves a run id or a qualification digest.

**The three ceilings between the attachment and the seat (Q3, Q4).**
1. Admission: `reason --attach` admits at most 64 files
   (`admission/attach.py:27`); the managed attached-evidence policy is
   HARD-CODED, not configuration — `maximum_sources=16`,
   `maximum_sources_per_pack=8`, `maximum_excerpt_bytes_per_source=262144`,
   `maximum_total_bytes=8 MiB` (`v6_policy.py:621-641`), and a dossier with
   more than 16 sources is refused at bind (`run_manifest.py:4353-4364`).
   A file per record (94 files) is therefore impossible; the attachment is
   THREE plain-text files — conjectures, proposals, objections — each record
   its own blank-line-separated paragraph, so admission mints ONE block per
   record (`parse.py:150-240`: a run of non-blank lines is one paragraph
   block, up to 4096 bytes, never split mid-line; no room body contains a
   blank line, a `#` line or a pipe-table line, and the longest is 1 038
   characters — M6). Three sources ≤ 8 per pack, so EVERY body is rendered
   in the frozen-evidence section on every conjecturer call.
2. The citable legend: `citable_legend(maximum_blocks=32, excerpt_chars=160)`
   is called with its defaults by `dr.src.citable_evidence`
   (`seat_sources/shipped.py:249-252`); the source declares no parameters.
   NOT configuration. The legend is what the exposure receipt is built from
   (`conj.py:1628-1665`), so only its 32 blocks are citable; a citation
   outside it is the typed `EVIDENCE_REF_NOT_EXPOSED` measure. PARKED (P2).
   Mitigated by ORDER, which is admission order (`_union_blocks`,
   `shipped.py:104-115`, walks the dossier's blocks in order; sources are
   admitted in sorted-path order, `attach.py:53-66`): the conjectures file
   sorts first, then the proposals file with every conjecture's
   refuted-if proposal before any other kind, so all 12 conjecture blocks
   and all 12 refuted-if blocks are citable, plus the first 8 of the
   remaining proposals. Objections are never cited by design (R9).
3. The section allocator: `Config.PACK_TOKEN_BUDGET` (default 2500,
   `config.py:732`) is set by `--config <partial YAML>` (`m2_rung.sh`,
   measured there; `config.py:802-813`) — configuration. Both evidence
   sections are droppable and compressible at priority 4 in the legacy
   layout; the organiser layout marks them NOT droppable, NOT compressible.
   Budget 24 000 tokens: the room is 53 493 characters ≈ 13 400 tokens at
   the allocator's 4 chars/token, the legend ≈ 1 500, the rest of the brief
   under 2 000; 24 000 tokens ≈ 96 000 characters, well inside the
   131 072-token window with the 8 192 completion cap. The knob MOVES the
   qualification subject digest (m2_rung.sh's own measurement), so each
   arm's home pays one battery. The allocation controller lists
   `PACK_TOKEN_BUDGET` and `VS_K` in its generator ledger but declares no
   envelope for either (`controller.py:46, 124-156`), so it cannot move them.

**Cycle scope (Q5).** Nothing configuration-shaped is cycle-scoped:
`DEEPREASON_SEAT_SHELL` is read at every render for the whole process. The
operations-parity road — `reason --cycles 1`, then `continue --budget
cycles=N-1` with the variable unset — is a configuration road in
principle, and the history tranche recorded `continue` refused between
cycles (`experiments/2026-09-03-change-provenance-history-channel/PARKED.md`
P1, `CONTINUE_TYPED_STOP_REQUIRED`). Decided (dominance: one variable per
arm, no unproven road on a live arm): the organiser shell runs for the
WHOLE run with the room attached throughout; the organiser directive
handles later cycles itself (carry only room conjectures not yet on the
record — the NEIGHBOURHOOD section lists what is — else abstain, which
`conjecturer.turn.v6` accepts as a meaningful outcome). The cycle-scoped
pairing is PARKED with a ready prompt (P3).

**The critic (Q3, R14).** The critic's default layout carries
`dr.evidence.citable` gated on `dr.premise-invitation`
(`seat_layouts.py:95-99`), and the invitation stands whenever the target's
problem has refuted candidates (`crit.py:1268-1280`, `premise_work_invited`).
So on a run with a bound dossier the default critic MAY be shown the
legend — ids and 160-character excerpts, never bodies (`dr.evidence.frozen`
is conjecturer-only). R14 says the critic does not see the room blocks on
this run. Decided: a registered critic pairing `seat.critic.evidence-blind-v1`
whose layout is the legacy critic layout minus `dr.premise-invitation` and
`dr.evidence.citable`, bound in ARM R only (ARM H keeps default shells per
R16). Disclosed difference between the arms on the critic side: ARM H's
critic may render an invitation note with no legend (it has no dossier);
ARM R's renders neither. The switch that WOULD show the critic the room —
a critic layout carrying `dr.evidence.frozen` — is PARKED (P4).

**The judged unit (Q6).** There is no `deepreason result`; `deepreason
results` prints typed counts (`cli/main.py:1305-1328`). The composed unit
is derived from the ROOT by a tranche tool, `compose_result.py`, with no
model in the loop: the seed problem's conjecturer artifacts by terminal
status (`findings.py:290-319` is the reader pattern), each accepted one
rendered as claim, mechanism and its counterconditions (from the envelope
JSON the artifact carries), the refuted ones listed with their attacker's
recorded case. One text per harness arm; ARM 0's unit is each call's
essay, as D8 had it.

**The soak case (Q7).** No committed case drives qwen3.5:397b. `epoch3` is
the launch configuration's SHAPE — solo, attached evidence ENABLED, engaged
control plane (`cycle_soak.py --list-cases`, M9) — and the case D8 used.
Disclosed: the soak proves the box and the managed path's shape, not the
organiser shell (no case binds a non-default shell). The organiser is
proven offline by S12's stub test instead.

**The credential (Q8).** Absent on this container (M10). R23 governs: moves
1–2 and the sealed PREREG are delivered; the launch scripts are committed
ready to run; no arm runs here. Said plainly in DELIVERY.md and RESULTS.md.

## Items

S1 (R1, C8, C12, C13): the organiser seat is a REGISTERED PAIRING, no new form.
    files: `src/deepreason/llm/seat_layouts.py` (a layout `seat-pack.conjecturer.organiser-v1`, a shell `seat.conjecturer.organiser-v1` pairing it with `conjecturer.turn.v6` and `role-prompt.organiser-v1`; a critic layout `seat-pack.critic.evidence-blind-v1` and shell `seat.critic.evidence-blind-v1`), registered in `register_shipped_layouts`; `src/deepreason/llm/seat_plugins.py` (one plugin `dr.output-contract.organiser`, section `output-contract`, added to `CONJECTURER_PLUGINS`); `src/deepreason/llm/role_prompts.py` (one template `role-prompt.organiser-v1`: legacy for every role, the conjecturer's `standard` and `compact_directive` replaced).
    before: two shipped shells; the conjecturer's only output contract asks for a distribution of diverse, atypical candidates.
    after: four shipped shells; defaults untouched (the goldens do not move).
    accept: `python -c "from deepreason.llm.seat_plugins import ensure_seeded; ensure_seeded(); from deepreason.llm.seat_sections import resolve_seat_shell, seat_shell_ids; s=resolve_seat_shell('conjecturer','seat.conjecturer.organiser-v1'); assert s.form_id=='conjecturer.turn.v6' and s.layout_id=='seat-pack.conjecturer.organiser-v1' and s.role_prompt_template_id=='role-prompt.organiser-v1'; c=resolve_seat_shell('argumentative_critic','seat.critic.evidence-blind-v1'); assert c.form_id=='argumentative_critic.compact.v1'; print(seat_shell_ids())"` -> prints four ids, exits 0; AND `python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py tests/test_role_prompt_registry.py -q` -> 0 failed.

S2 (R2, R16, R20, R21): the launch scripts for ARM H and ARM R, committed and ready.
    files: `<T>/runs/setup_and_qualify.sh` (per home; profile line as `armM.sh`/`setup_and_qualify.sh` of the newest launches: qwen3.5:397b, reasoning none, 131072/8192; `qualify --yes --attached-evidence --concurrency 2` for ARM R's home, `qualify --yes --concurrency 2` for ARM H's), `<T>/runs/armH.sh`, `<T>/runs/armR.sh` (both `--config <T>/runs/config.yaml`, `--cycles 4 --token-budget 800000`, the frozen D8 question text; ARM R adds `--attach <T>/attachment/` and exports the two selectors), `<T>/runs/config.yaml` (`PACK_TOKEN_BUDGET: 24000`, nothing else), `<T>/runs/chain.sh` (soak → ARM H → ARM R, detached, snapshot loop armed), `<T>/runs/snapshot.sh`.
    accept: `bash -n` on every script -> exit 0; `grep -c 'set -a; . \$D/env; set +a' <T>/runs/armR.sh` -> 1; `grep -q 'DEEPREASON_SEAT_SHELL=conjecturer=seat.conjecturer.organiser-v1,argumentative_critic=seat.critic.evidence-blind-v1' <T>/runs/armR.sh` -> exit 0; `! grep -q DEEPREASON_SEAT_SHELL <T>/runs/armH.sh` -> exit 0.

S3 (R3, C2, C3, C15): the converter.
    files: `<T>/tools/room_to_attachment.py` — reads `<ROOM>` through `minireason.loop.Session` and `minireason.records.mini_records` (import only; `mini/` unchanged), writes `<T>/attachment/01-conjectures.txt`, `02-proposals.txt`, `03-objections.txt`: one paragraph per record, blank-line separated, header line `<KIND> id=<room record id, 16 hex> cycle=<n> about=<conjecture id, 16 hex>` (no `about=` on conjectures), then the body VERBATIM (labels included, since they are part of the recorded body). Proposals ordered: every conjecture's refuted-if first (room order), then forbids, must-not, predicts. Cycle = the index of the Conj event whose seq precedes the record (M7: Conj events at seq 2, 31, 60).
    accept: `python <T>/tools/room_to_attachment.py <ROOM> <T>/attachment --json <T>/attachment/CONVERSION.json` -> prints `records 94 (12 conjectures, 46 proposals, 36 objections)`; `python - <<EOF` check that every paragraph body equals its record's content byte for byte -> `verbatim 94/94`.

S4 (R4): the attachment and its digest are committed.
    files: `<T>/attachment/*.txt`, `<T>/attachment/CONVERSION.json` (per-record: kind, id, cycle, about, chars, sha256 of the body), `<T>/attachment/ATTACHMENT.sha256` (sha256 of each file and of the whole directory listing).
    accept: `sha256sum -c <T>/attachment/ATTACHMENT.sha256` -> all OK; `git ls-files <T>/attachment | wc -l` -> 5.

S5 (R5): the dry attach, measured offline.
    files: `<T>/proof/dry_attach.py` — admits the attachment through `admit_attachment_paths` (the same function `reason --attach` calls, `cli/main.py:2562-2570`) against the D8 question, and reports sources, blocks, tiers, refusals and the dossier digest; then, against the stub (S12's fixture with THIS dossier bound and the managed policy bounds of `v6_policy.py:636-641`), renders one organiser call and reports: blocks in the legend (shown), blocks withheld, sources in the frozen pack, `excluded_source_ids`, and the pack's byte size. Output committed as `<T>/proof/DRY_ATTACH.txt`.
    accept: `python <T>/proof/dry_attach.py` -> `sources 3 blocks 94 refusals 0`; `legend shown 32 withheld 62`; `frozen pack sources 3 excluded 0`; the file exists with those lines.

S6 (R6, C4): the pack sized, and the part that is not configuration parked.
    files: `<T>/runs/config.yaml` (S2); `<T>/PARKED.md` P2 (the legend cap and excerpt length are code, not configuration — prompt: a parametrised `dr.src.citable_evidence` 1.1.0 and a bundle selected by `DEEPREASON_SEAT_SOURCE_BUNDLE`).
    accept: `deepreason --config <T>/runs/config.yaml config | grep '^PACK_TOKEN_BUDGET:'` -> `PACK_TOKEN_BUDGET: 24000`; S5's rendered organiser brief carries the frozen-evidence section with all three sources' bodies UNCOMPRESSED (`grep -c 'BEGIN UNTRUSTED SOURCE DATA' <T>/proof/ORGANISER_BRIEF.txt` -> 3, and no `WITHHELD`/compressed disposition on `frozen-evidence-context` or `citable-evidence-blocks` in the section receipts); `grep -q '^## P2' <T>/PARKED.md`.

S7 (R7, A1): the pairing binds the form the managed path actually reaches.
    files: as S1. `form_id="conjecturer.turn.v6"`; the docstring beside the shell states that the brief named `reasoning.conjecturer.compact.v2` and why `turn.v6` is the form the seat fills (its candidate is the same `ReasoningCandidateProposal`).
    accept: `python -c "from deepreason.workloads.text import ReasoningCandidateProposal as P; from deepreason.llm.wire import ReasoningConjecturerTurnWireV6 as W; assert W.model_fields['candidates'].annotation == list[P]"` -> exit 0; `grep -n 'compact.v2' src/deepreason/llm/seat_layouts.py` -> the recorded contradiction, ≥1 line.

S8 (R8, A2): registered in `seat_layouts.py`, said so, and the loader gap parked.
    files: as S1; `<T>/PARKED.md` P1 (the managed path does not load `<DEEPREASON_HOME>/seat_plugins/` — one call site, `shallow.py:71`; prompt: call `load_operator_plugins` in the managed preparation and record its two lists on the run, as the reduced engine does).
    accept: `grep -rn 'load_operator_plugins(' src/deepreason --include=*.py | grep -v 'def ' | wc -l` -> 1 (unchanged by this tranche); `grep -q '^## P1' <T>/PARKED.md`.

S9 (R9, C12): the organiser brief.
    files: `seat_plugins.py::_OrganiserOutputContract` renders, in this order: (1) `DIRECTIVE: ORGANISE, DO NOT INVENT.`; (2) the room's shape — the three sources, the header grammar, and that a proposal's `about=` names the conjecture it binds; (3) one candidate per room conjecture worth carrying, at most `{vs_k}` this turn; on a later turn only conjectures not already in NEIGHBOURHOOD, else abstain; (4) claim and mechanism condensed from the conjecture's own block and sharpened by its objections; (5) every countercondition taken from that conjecture's proposals — refuted-if as written; "forbids X"/"must not X" → refuted if X; "predicts X" → refuted if not X; (6) `evidence_refs`: the conjecture's block id and its proposals' block ids, ONLY ids that appear in CITABLE EVIDENCE BLOCKS (an id outside that list is recorded as a failed citation); (7) a conjecture with no proposal is left out and named in the candidate's `uncertainties`; (8) typicality 0.5 unless the room gives a reason; (9) nothing that is not in the blocks; (10) the discharge clause verbatim from the legacy contract when open criticisms are supplied. The layout: legacy minus `dr.school-stance`, `dr.crossover`, `dr.complement-directive`, `dr.diversity-specifications`, `dr.history.v1`; `dr.evidence.frozen` and `dr.evidence.citable` at priority 2, `droppable=False`, `compressible=False`; `dr.output-contract.organiser` in the legacy contract's slot. The wording template's conjecturer prose: the organiser's standing instruction (carry, do not invent; the harness adjudicates), the JSON-only demand unchanged.
    accept: `<T>/proof/ORGANISER_BRIEF.txt` (S11) contains `ORGANISE, DO NOT INVENT`, `refuted if not`, `uncertainties`, `0.5`, and does NOT contain `COMPLEMENT DIRECTIVE`, `DIVERSITY SPECIFICATIONS` or `Include atypical candidates`.

S10 (R10): stated on the record.
    files: `<T>/RESULTS.md` §"What the form excludes on this record": every one of the 12 room conjectures has a refuted-if proposal (`<T>/attachment/CONVERSION.json`), so the form's mechanism and ≥1-countercondition requirements exclude nothing; the statement carries the count from the converter's output.
    accept: `python -c "import json; d=json.load(open('<T>/attachment/CONVERSION.json')); c=[r for r in d['records'] if r['kind']=='conjecture']; p=[r for r in d['records'] if r['kind']=='proposal' and r['label']=='refuted-if']; assert {r['id'] for r in c} == {r['about'] for r in p}; print(len(c), len(p))"` -> `12 12`; `grep -q '12 of 12' <T>/RESULTS.md`.

S11 (R11): the rendered brief, shown before any live call.
    files: `<T>/proof/render_brief.py` — S12's fixture with the real attachment bound, `PACK_TOKEN_BUDGET=24000`, the organiser shell selected, ONE conjecturer dispatch against a mock endpoint that returns an abstention; writes the exact prompt the seat would receive to `<T>/proof/ORGANISER_BRIEF.txt` and the section receipts to `<T>/proof/ORGANISER_RECEIPTS.json`. Committed before PREREG.md's sealing commit.
    accept: `wc -c <T>/proof/ORGANISER_BRIEF.txt` -> more than 55 000; `git log --format=%H -1 -- <T>/proof/ORGANISER_BRIEF.txt` precedes `git log --format=%H -1 -- <T>/PREREG.md` in history.

S12 (R12, C3): the stub test.
    files: `tests/test_organiser_seat.py` — builds a root the way `tests/test_p4_citable_evidence.py::_evidence_root` does, but binding a dossier admitted from a COMMITTED fixture copy of the three attachment files (`tests/fixtures/organiser_room/`, the same bytes as `<T>/attachment`, pinned by sha256 in the test), with the managed policy bounds; selects the organiser shell through `DEEPREASON_SEAT_SHELL`; dispatches `conj` against a mock endpoint returning two organiser candidates. Asserts: (a) both admit through the ordinary path (registered conjecturer artifacts on the record, no code path named "organiser" on the way in); (b) each candidate's counterconditions are commitments the artifact carries (`reason-counter@…` ids, `draft_countercondition_commitments` shape); (c) the first candidate cites the conjecture block and its refuted-if block — both `evidence-citation:verified` measures; the second cites a block id from the objections file that the legend did not show — one `evidence-citation:EVIDENCE_REF_NOT_EXPOSED` measure, and the candidate still admits (a measure, never a status); (d) a citation to an id that resolves to no block at all → `EVIDENCE_REF_UNKNOWN_BLOCK`; (e) the rendered brief contains the organiser directive and not the legacy one; (f) the section receipts record `dr.output-contract.organiser` rendered and `dr.complement-directive` absent from the layout. Mutation companion: with the shell unbound, (e) fails.
    accept: `python -m pytest tests/test_organiser_seat.py -q` -> `N passed, 0 failed` (N ≥ 6); the mutation is a test in the same file that asserts the legacy brief under no binding.

S13 (R13, A5): decided and disclosed.
    files: this document (above); `<T>/PARKED.md` P3 (cycle-scoped pairing: two roads priced — a per-cycle shell selection recorded on the run, or `reason --cycles 1` + `continue` proven offline first); `<T>/runs/armR.sh` runs the organiser for the whole run.
    accept: `grep -q '^## P3' <T>/PARKED.md`; `grep -c 'continue' <T>/runs/armR.sh` -> 0.

S14 (R14): the critic does not see the room on ARM R.
    files: as S1 (`seat.critic.evidence-blind-v1`); `tests/test_organiser_seat.py` asserts the blind critic layout has neither `dr.premise-invitation` nor `dr.evidence.citable` and is otherwise the legacy critic layout entry for entry; `<T>/PARKED.md` P4 (the switch that would show the critic the room bodies: a critic layout carrying `dr.evidence.frozen`).
    accept: `python -c "from deepreason.llm.seat_plugins import ensure_seeded; ensure_seeded(); from deepreason.llm.seat_sections import resolve_seat_pack_layout; ids=[e.plugin_id for e in resolve_seat_pack_layout('argumentative_critic','seat-pack.critic.evidence-blind-v1').entries]; assert 'dr.evidence.citable' not in ids and 'dr.premise-invitation' not in ids and 'dr.target' in ids"` -> exit 0; `grep -q '^## P4' <T>/PARKED.md`.

S15 (R15, R17, R18, R19): PREREG.md, sealed.
    files: `<T>/PREREG.md` — PREREG_D8's form: §0 what is fixed (model, input `runs/input-d8` by digest, reasoning field, config.yaml, cycles 4, token budget 800 000, selectors), §1 ARM 0 (the three recorded calls, reused, sha256 of `d8/arm0/call-*.json` pinned), §2 ARM H, §3 ARM R, §4 the judged unit (`compose_result.py`'s deterministic composition; ARM 0 = each essay), §5 judging (the copied five criteria verbatim; 3 judges, median, contested flag, blinding, keymap shut), §6 length control with the overlap clause (D8 §4's estimators; INCONCLUSIVE when no pooled quintile holds both arms being compared), §7 the decision rule: ARM R is MATERIALLY BETTER iff it is BETTER than ARM 0 under the rule AND BETTER than ARM H under the rule; otherwise NULL (indistinguishable from either) or WORSE, reported as such, §8 predictions (no quality direction; length: composed units longer than an essay is NOT predicted — the composition is bounded by the survivors; cost: ARM R's conjecturer-seat tokens exceed ARM H's by at least the room's size per call), §9 the failure budget (6 live calls beyond the plan, S6-style ledger in RESULTS.md), §10 order of operations, §11 residue in advance (one question, one model, one room; same-model judging; n; the legend cap; the soak covers the shape not the shell).
    accept: PREREG.md exists; the commit adding it carries `sha256` of the file in its message; `sha256sum <T>/PREREG.md` equals that value; `git log --format=%s -1 -- <T>/PREREG.md | grep -c sha256` -> 1.

S16 (R16): the arms' scripts (S2) and the instruments: `<T>/tools/compose_result.py`, `<T>/tools/judge_organiser.py` (a copy of `d8/judge_d8.py` whose ONLY changes are `harvest` and paths), `<T>/tools/analyse_organiser.py` (D8's analyser over three arms, pairwise R–0 and R–H).
    accept: `python <T>/tools/compose_result.py --self-test` -> exit 0 (composes a committed full-harness root, `experiments/2026-09-03-change-provenance-history-channel/runs/home-m1/runs/run-ad41064484366337ed61a9d5a58de58f`, and prints its survivor count); `python <T>/tools/judge_organiser.py --help` -> exit 0; `diff <(sed -n '/^CRITERIA = /,/^"""$/p' <T>/tools/judge_organiser.py) <(sed -n '/^CRITERIA = /,/^"""$/p' experiments/2026-09-05-change-mini-isolation-programme/d8/judge_d8.py)` -> empty.

S17 (R17): the judged unit is composed, never chosen.
    files: `<T>/tools/compose_result.py` — deterministic; reads only the root; no model call.
    accept: `grep -c 'urllib\|requests\|ollama' <T>/tools/compose_result.py` -> 0.

S18 (R18): blinding and length as D8.
    files: as S16; `<T>/tools/judge_organiser.py reveal` refuses without `scores.json`.
    accept: `grep -q 'keymap' <T>/tools/judge_organiser.py && grep -q 'quintile' <T>/tools/analyse_organiser.py` -> exit 0.

S19 (R19): the verdict rule in PREREG §7 (S15).
    accept: `grep -q 'MATERIALLY BETTER' <T>/PREREG.md`.

S20 (R20, A7): soak and launch discipline.
    files: `<T>/runs/chain.sh` runs `python -u scripts/cycle_soak.py --case epoch3` and refuses to launch on a non-zero exit; the soak's log is committed as `<T>/runs/soak.log` when it has been run on this tree.
    accept: `grep -q 'cycle_soak.py --case epoch3' <T>/runs/chain.sh`; `<T>/runs/soak.log` ends `rc=0` (run here, offline — it needs no key).

S21 (R21): env discipline.
    accept: `git check-ignore -q <T>/env` -> exit 0 (M10); no committed file under `<T>` contains `OLLAMA_API_KEY=` followed by a value: `! git grep -n 'OLLAMA_API_KEY=[A-Za-z0-9]' -- <T>` -> exit 0.

S22 (R22): the failure-budget ledger section exists in RESULTS.md with 0 spent.
    accept: `grep -q 'Failure budget' <T>/RESULTS.md`.

S23 (R23, A8): no key → delivered without the runs, said plainly.
    accept: `grep -q 'no credential' <T>/DELIVERY.md`; `grep -q 'not run' <T>/RESULTS.md`.

S24 (R24): RESULTS.md, honest ledger, dated segments: what the record shows (the offline measurements, the rendered brief, the stub proofs), what it does not (no live arm ran; one question, one model, one room).
    accept: `grep -q '^## 2026-09-06' <T>/RESULTS.md`.

S25 (R25, C5, C6, C7): validation and delivery through the workflow; the full gate once at the boundary (code under `src/` and `tests/` changes); `docs/map/INV-seat-section-plugins.md` moves in the same commit as `seat_layouts.py` (a paragraph on the four shipped shells and a `check:` that the organiser shell pairs `turn.v6` with the organiser layout and that the blind critic layout omits the two evidence entries); the packaging surface is untouched (no CLI, MCP or entry-point change) — smoke not owed.
    accept: VALIDATION.md verdict PASS; the gate line `N passed, 0 failed`; `python tools/docs_verify.py` 0 failed.

## Assumptions (operator may override)

A1 (Q1): the organiser pairs `conjecturer.turn.v6`, the form the managed conjecturer fills; `reasoning.conjecturer.compact.v2` does not reach that path and compiles to the same proposal type. Assumed, operator may override — the property (a commitment-bearing candidate on an EXISTING form) is delivered.
A2 (Q2): registered in `seat_layouts.py`/`seat_plugins.py`/`role_prompts.py`, per the brief's fallback clause; the loader gap is parked (P1).
A3 (Q3/Q4): three files, conjectures/proposals/objections; refuted-if proposals ordered first so every conjecture's refutation condition is citable under the 32-block legend cap; `PACK_TOKEN_BUDGET: 24000` in BOTH arms' config (one config, one battery per home, only the treatment differs). Assumed, operator may override.
A4: `VS_K` stays at its default 6 in both arms; the organiser carries at most 6 per turn and the rest on the next turn. Raising it would change ARM H's generation width too. Assumed, operator may override.
A5 (Q5): whole-run organiser; cycle-scoped pairing parked (P3).
A6 (Q6): the judged unit is the deterministic composition in `compose_result.py`; survivors rendered with claim, mechanism, counterconditions; refuted positions listed with their attacker's case; no model composes. Assumed, operator may override.
A7 (Q7): `epoch3` is the soak case; it proves the shape, not the shell.
A8 (Q8): no key on this container; R23 applies. If the operator places `<T>/env`, `chain.sh` is the one command to run.
A9: cycles 4, token budget 800 000 per harness arm (the M1 arms ran 4 cycles at 600 000 with a 2 500-token pack; the organiser's pack is ten times larger).
A10: the room's optional labels (`[angle: …]`, `[kind: …]`, `[would settle: …]`) stay INSIDE the verbatim bodies — they are part of what the seat recorded — and the converter's header line carries the kind and label separately so the organiser can read them without parsing.
A11: ARM R's wording template (`role-prompt.organiser-v1`) differs from legacy ONLY in the conjecturer's entries; every other role's prose is byte-identical (asserted in the stub test).

## Questions for operator (STOP if non-empty)

none — every fork above is decided by the record or by dominance under the
operator's recorded values, and recorded as an assumption.

## Out of scope (explicit)

- A parametrised citable-evidence source (the legend cap): not requested — P2.
- Loading `<DEEPREASON_HOME>/seat_plugins/` on the managed path: not requested — P1.
- Per-countercondition block pointers: C3 says park — P5.
- A critic that reads the room bodies: R14 says the opposite — P4.
- Any change under `mini/`, `src/deepreason/evidence/`, `src/deepreason/rules/`, `src/deepreason/admission/`: C2, C3.
- Re-running ARM 0: R16 says reuse.
- The room's P1/P2 and mini's P10/P11: C4.

## Frozen-surface contact forecast

none expected — `tools/blast_radius.py --files src/deepreason/llm/seat_layouts.py src/deepreason/llm/seat_plugins.py --symbols register_shipped_layouts ensure_seeded CONJECTURER_LEGACY_LAYOUT`, run 2026-09-06 on `d3f047932`:

    frozen_surface_verdict: CLEAR
    frozen_surface_contacts: []
    frozen_adjacent_contacts: []
    reachability: register_shipped_layouts REACHABLE; ensure_seeded REACHABLE; CONJECTURER_LEGACY_LAYOUT UNKNOWN (a module constant, not a def — the manual grep below covers it)

`role_prompts.py` is added to the target set at the first execute step and the
gate re-run there (dr-execute-step rule 6); it is owned by
`DR-INV-seat-section-plugins`, not by any frozen document, and imports only
`seat_sections`.

## Blast-radius census

Pasted from the same run (`consumers`), every hit classified:

- `src/deepreason/llm/seat_plugins.py` → `tests/test_render_layout_policy.py:120, :190`; `tests/test_seat_section_architecture.py:74`; `tests/test_seat_section_citation.py:155` — MUST NOT MOVE (they read the seeded set by id or count sections built; a new plugin appended to `CONJECTURER_PLUGINS` adds a registered id and builds no section). Verified by running them in the ring.
- `ensure_seeded` → `tests/test_discharge_channel.py:225, :227`; `tests/test_seat_section_architecture.py:91, :101`; `tests/test_seat_section_citation.py:24, :39`; `tests/test_seat_section_home.py:337, :343`; `tests/test_seat_section_record.py:22, :31`; `tests/test_seat_section_template.py:164, :168, :190, :194`; `tests/test_seat_shell_swap.py:27, :43` — MUST NOT MOVE (seeding is idempotent; four more registrations).
- `CONJECTURER_LEGACY_LAYOUT` → `tests/test_discharge_channel.py:224, :234`; `tests/test_seat_section_architecture.py:90, :128`; `tests/test_seat_section_citation.py:21, :86, :140`; `tests/test_seat_section_record.py:44, :47` — MUST NOT MOVE (the legacy layout is not edited; the organiser layout is built from a filtered COPY of its entries).
- map checks: `docs/map/CON-packs-and-token-economy.md:44, :45, :103, :136, :160, :237, :278`; `docs/map/INV-render-layout.md:215`; `docs/map/INV-seat-section-plugins.md:4`; `docs/map/SEAM-rules-x-scratch.md:68`; `docs/map/SEAM-schools-x-scratch.md:286` — MUST NOT MOVE (they pin the LEGACY layout's shape and sharing; `:103-111` asserts the three shared plugins and their priorities on the two legacy layouts by id). `INV-seat-section-plugins.md` is EXPECTED TO MOVE by addition only (a new paragraph and check, S25).
- manual cross-check for the `UNKNOWN` symbol and the string ids: `grep -rn 'seat-pack.critic.legacy-v0\|seat.critic.legacy-v0\|seat.conjecturer.legacy-v0' docs/map tests` → 8 hits, all pins on the legacy ids, none on a count of shells → MUST NOT MOVE. `docs/map/SUB-minireason.md:394` unions `seat_shell_ids()` with mini's names to assert disjointness → MUST NOT MOVE (the four new ids are not mini names).
- `tests/test_role_prompt_registry.py` (`test_the_legacy_template_covers_every_role_roles_declares`) → MUST NOT MOVE (resolves the DEFAULT; the organiser template is a second registration).
- the goldens (`tests/test_conj_pack_legacy_golden.py`, `tests/test_crit_pack_legacy_golden.py`) → MUST NOT MOVE (defaults untouched).
- `tests/test_seat_section_architecture.py::test_limb3_the_shell_carries_nothing_that_could_buy_standing` → MUST NOT MOVE (the new shells carry the same six fields).
- qualification subject digest, wheel-smoke pins → MUST NOT MOVE (no `Config` field, no CLI/MCP change).

## Measurements

M1: `python tools/blast_radius.py --files src/deepreason/llm/seat_layouts.py src/deepreason/llm/seat_plugins.py …` → `frozen_surface_verdict: CLEAR`, both contact lists empty — supports "none frozen".
M2: `grep -n -E 'compact.v2|configured_turn_contract' src/deepreason/rules/conj.py` → `2340-2353`: `configured_turn_contract if active_v6 … "reasoning.conjecturer.compact.v2" if reasoning else contract_id`; `grep -n 'class ReasoningConjecturerTurnWireV4' -A6 src/deepreason/llm/wire.py` → `candidates: list[ReasoningCandidateProposal]` — supports A1.
M3: `grep -rn 'load_operator_plugins' src/deepreason --include=*.py | grep -v 'def '` → `src/deepreason/shallow.py:71`, `:73` only — supports A2.
M4: `sed -n 621,641p src/deepreason/v6_policy.py` → `maximum_sources=16, maximum_total_bytes=8 MiB, maximum_excerpt_bytes_per_source=262_144, maximum_sources_per_pack=8`; `attach.py:27` → `MAX_ATTACHMENT_FILES = 64` — supports A3 (three files).
M5: `sed -n 192-232p src/deepreason/evidence/render.py` → `maximum_blocks: int = 32, excerpt_chars: int = 160`; `shipped.py:249-252` → called with no parameters — supports P2.
M6: the room root read through `minireason`: `blank-line bodies: []`, `max chars 1038`, `hash lines 0`, `pipe lines 0`; totals `12 / 36 / 46`, `chars 53493` — supports one block per record and the pack size.
M7: Conj event seqs `[2, 31, 60]` — the cycle boundaries the converter uses.
M8: `deepreason --config <cfg> config` echoes `PACK_TOKEN_BUDGET` (m2_rung.sh's guard) and `config.py:802-813` loads a partial YAML — supports "the allocator budget is configuration".
M9: `python scripts/cycle_soak.py --list-cases` → `epoch3 … solo … attached evidence ENABLED, engaged control plane v3` — supports A7.
M10: `ls experiments/live_research_*/env` → none; `env | grep -c OLLAMA_API_KEY` → 0; `git check-ignore -v <T>/env` → `.gitignore:50:experiments/**/env` — supports A8 and S21.
M11: ring baseline on the unchanged tree: `python -m pytest tests/test_seat_shell_swap.py tests/test_seat_section_home.py tests/test_role_prompt_registry.py tests/test_p4_citable_evidence.py tests/test_seat_section_architecture.py -q` → `92 passed`.
M12: `grep -n -A22 'def _premise_invited_problem' src/deepreason/rules/crit.py` → the legend reaches the critic iff `premise_work_invited(harness, pid)` — supports S14.

## Budget

~420 lines under `src/`, `tests/` and `docs/map/` — `python3 -c "print(sum([50,70,40,230,30]))"` → `420` (seat_layouts 50, seat_plugins 70, role_prompts 40, tests 230, map 30); ceiling for `tools/diff_budget.py --paths src tests docs/map`: 450. Tranche artefacts under `<T>` (converter, attachment, proofs, instruments, scripts, PREREG, ledgers) are experiment content outside that ceiling, ~1 500 lines. Commits: one per checklist `[COMMIT]` step, about ten. Frozen surfaces touched: none.

Rubric: 6/6 yes — every R has an item with a machine-decidable accept; census pasted and classified; frozen forecast recorded from the gate; every named mechanism traced (two did not reach: compact.v2 → A1, seat_plugins dir → A2; one did not exist: `deepreason result` → A6); not a DESIGN-AND-STOP; nothing untraceable.

## Amendments (append-only)

**Amendment 1 (2026-09-06, found at CHECKLIST step 6, recorded here per
dr-execute-step rule 3).** A3's ordering claim is FALSE. The citable legend
does show the dossier's first 32 blocks, but a dossier's blocks are sorted by
CONTENT ID at admission (`src/deepreason/admission/parse.py:577`,
`blocks=tuple(sorted(blocks, key=lambda block: block.id))`), not by file or
record order, so file naming and the refuted-if-first ordering steer
nothing. Measured on the committed attachment (the stub test's own
assertion): the 32 citable blocks are 7 conjectures, 13 proposals (1
refuted-if) and 12 objections; 62 blocks are withheld from the legend,
among them 5 conjectures and 11 refuted-if proposals. What does NOT change:
every body is still rendered whole in the frozen-evidence section (3 sources
of 3, nothing excluded), so the organiser READS the whole room; what changes
is how much of it a candidate can CITE without the typed
`EVIDENCE_REF_NOT_EXPOSED` measure. The organiser directive already tells
the seat to cite only ids in the legend and to name the rest in
`uncertainties`. Disposition: no design change (C3, C4; the brief's own
"run with what the pack shows, disclosed"); the attachment's bytes and the
converter's output are unchanged; the converter's docstring now says why
the order is kept (the human reader of the frozen section); PARKED P2
carries BOTH the cap and the order; PREREG §11 and RESULTS.md state the
measured citability. S5's accept line `legend shown 32 withheld 62` stands;
its "which" is now also reported.

**Amendment 2 (2026-09-06, CHECKLIST step 7, the diff-budget gate).**
`tools/diff_budget.py d3f047932 --ceiling 450 --paths src tests docs/map`
reported EXCEEDED: `src 214, tests 885, docs/map 33, total 1132`. Two
causes, disposed separately. (1) 365 of the `tests` lines were a byte-for-
byte COPY of the attachment under `tests/fixtures/organiser_room/` — data,
not code; the copy is removed and the test reads the committed attachment
from the tranche directory instead (`git ls-files` knows it; the sha256 pins
stay), so nothing is lost and nothing is duplicated. (2) The test file is 520
lines against an estimate of 230 and `src/` is 214 against 160: twelve
proofs with their docstrings, and the layouts' rationale comments. Decided
without asking (dominant under the operator's recorded values — the stub test
IS R12's deliverable and trimming proof to fit an estimate would ship less
evidence, not less machinery): the ceiling for `src tests docs/map` is raised
from 450 to 800; the re-measured total is stated in CHECKLIST step 7.
Override any time. No scope moved: the same three source files, one test
file, one map document.

## Amendment 3 (2026-09-06, the launch window) — the reading of "It needs a test run now. Propose some for a single model run and test against bare model. 500k tokens"

**The reading (R27).** ONE harness run — the sealed ARM R (`runs/armR.sh`: the
full harness, the room attached, the organiser seat, the evidence-blind
critic) — against the BARE model in two forms: ARM 0 as sealed (three recorded
plain calls, reused by digest, never respent) and a NEW ARM 0R: the same
model, the same frozen question, the room's three attachment files pasted
verbatim into the user message after the question — no harness, no schema,
no system prompt, reasoning off, `max_tokens` 8192 (PREREG_D8 §1's call shape
plus the room text) — three calls. ARM H (the harness alone) is DEFERRED, not
deleted. "500k tokens" is ARM R's ceiling: `--token-budget 500000`, cycles 4
as sealed.

**Budget prediction (R28), from the record.** The M1 control arm (same model,
same question family, 4 cycles, pack 2 500, ceiling 600 000) spent 541 666
tokens: 48 conjecturer calls (394 112; mean 8 210) and 88 critic calls
(147 554) — about 135 000 per cycle, 12 conjecturer calls per cycle across the
seed and its derived problems. ARM R's organiser brief is ~23 000 prompt
tokens (`proof/ORGANISER_RECEIPTS.json`: 91 795 bytes) but only the SEED
problem's calls render the frozen room (the frozen-evidence source is gated on
the epoch problem; derived problems get the 6 113-byte legend only), so a
cycle costs roughly 135 000 plus ~17 000 per seed-problem conjecturer call.
At 2–4 seed calls per cycle that is ~170 000–200 000 per cycle: the 500 000
ceiling ends the run in CYCLE 3 (registered prediction), CYCLE 2 if the seed
problem is called more often than that, and reaching cycle 4 would falsify
the estimate that the room costs the run at least 35 000 tokens per cycle.

### Items

S26 (R26, R33): the launch. `runs/chain.sh` detached from the repository root with the snapshot loop armed; soak first; ARM R then ARM 0R.
    accept: `runs/chain.log` carries `soak rc=0`, ARM R's `rc=0` and `root=…`, ARM 0R's `rc=0`; the newest root under `runs/home-r/runs/` has `run-status.json` with `state: completed`.
S27 (R28): `runs/armR.sh` line 26: `--token-budget 800000` → `--token-budget 500000`; nothing else in that file moves.
    accept: `grep -c -- '--token-budget 500000' runs/armR.sh` -> 1; `git diff <pre-launch base> -- runs/armR.sh | grep -c '^[-+]' ` -> 2 (one line out, one in).
S28 (R29): PREREG.md Amendments 1–4 appended (ceiling + prediction; ARM 0R; ARM H deferred; the pairwise rule and the room-content reading), instruments' sha256s pinned, re-sealed by sha256 in the commit message.
    accept: `sha256sum PREREG.md` equals the digest in `git log -1 --format=%B -- PREREG.md`; `grep -c '^## Amendment' PREREG.md` -> 4 sections (one heading with four numbered amendments is accepted).
S29 (R30): `tools/judge_organiser.py harvest` reads a fourth arm `ARM0R-room-bare` from `runs/arm0R/call-*.json` (pinning each file's sha256 into the keymap) and treats a missing ARM H as deferred (a notice, not a refusal); `tools/analyse_organiser.py` reports R vs 0 and R vs 0R, applies §7 pairwise, prints the room-content reading when R is BETTER than 0 but not BETTER than 0R; the `CRITERIA` block byte-identical to D8's.
    accept: the sealed `diff` of the CRITERIA blocks is empty; `python tools/judge_organiser.py --help` and `python tools/analyse_organiser.py --help` exit 0; `grep -c 'ARM0R-room-bare' tools/judge_organiser.py tools/analyse_organiser.py` -> ≥1 each.
S30 (R31): `runs/arm0R.sh` + `runs/arm0R.py` (the D8 `arm0.py` call shape; the user message = question + blank line + the three files' bytes verbatim, in name order; records `request`, `response`, `usage`, `finish_reason`, `content`, the attachment digests and the prompt's sha256 per call; writes `runs/arm0R/call-{1,2,3}.json` and `ARM0R_RESULT.json`); `runs/chain.sh`: lines 14 (mkdir), 21 (ARM H's setup) and 23 (ARM H's arm) removed, ARM 0R appended after ARM R — the amendment names the lines.
    accept: `bash -n runs/arm0R.sh runs/chain.sh` exit 0; `python runs/arm0R.py --dry-run` prints the prompt's byte count and sha256 without a call; `! grep -q 'armH.sh' runs/chain.sh`; `grep -c 'arm0R.sh' runs/chain.sh` -> 1.
S31 (R32): the credential. `git check-ignore -q env`; mode 600; never committed, never printed.
    accept: `git check-ignore -q env` exit 0; `stat -c %a env` -> 600; `! git grep -n 'OLLAMA_API_KEY=[A-Za-z0-9]' -- .` exit 0 on every commit of this window.
S32 (R33): typed outcomes only. ARM R judged on `run-status.json` (`state`, `stop_reason`), `deepreason results <root> --json --verify` (0 violations, replay digest equal), the admission summary's dossier digest `2a49cd52…`, and the organiser-rendered count armR.sh prints (0 → INVALID, not judged). ONE relaunch only for a pre-cycle-1 transport death, disclosed.
    accept: RESULTS.md's segment quotes each of these from the record.
S33 (R34): harvest → score → reveal → analyse, in that order; `reveal` refuses without `blind/scores.json`.
    accept: `blind/scores.json` committed; `git log` shows the reveal output in RESULTS after the scores' commit.
S34 (R35): RESULTS.md dated segment with every listed content; ARM R's composed unit quoted whole in an appendix; NULL in the word NULL.
    accept: `grep -c '^## 2026-09-06' RESULTS.md` -> 2; `grep -q 'Appendix' RESULTS.md`; `grep -q 'Failure budget' RESULTS.md`.
S35 (R36): scope. `git diff --stat <pre-launch base>..HEAD -- src mini tests` empty; `sha256sum -c attachment/ATTACHMENT.sha256` OK; no gate run.
    accept: the two commands' outputs pasted in VALIDATION.md.
S36 (R36, R25): VALIDATION.md and DELIVERY.md re-issued for this window with the table extended to R26–R36.
    accept: DELIVERY.md's table has rows R1–R36.

### Assumptions (operator may override)
A12: ARM 0R's user message is the question, one blank line, then the three files' contents verbatim in name order separated by blank lines — no label, no instruction, so the bare model sees the room and nothing that tells it what the room is beyond each record's own header line. Assumed, operator may override.
A13: ARM 0R's three calls count as the plan, not the failure budget; the attached-evidence battery is the plan and is not counted in the 500 000.
A14: the pre-launch base for the diff checks is the commit that seals PREREG Amendments 1–4.

### Frozen-surface contact forecast
none — no file under `src/` moves (R36); `tools/blast_radius.py` is not owed for tranche artefacts.

### Budget
~0 lines under `src`/`tests`/`docs/map`; ~250 lines of tranche scripts and instrument edits; the run roots and `blind/` as evidence.

Rubric: 6/6 yes — every R26–R36 has an item with an accept; no census owed (no code); no frozen contact; the named mechanisms (armR.sh, chain.sh, judge/analyse, D8's arm0.py) exist and are the files edited; not DESIGN-AND-STOP; nothing untraceable.
