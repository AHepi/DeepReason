# Fix: give the authority census the one arm the defended trial needs

**STATUS: STOPPED FOR A FROZEN-SURFACE GRANT. No production code is changed.**
The change site is inside `src/deepreason/verification/`, which
`DR-INV-frozen-surfaces` surface 3 owns. The grant request is in §6, in the
standard stop format. Nothing below has been implemented.

Guarantee restored: **a v6 work transaction the frozen manifest authorised is
not reported as exceeding its authority** — for the defended trial's provider
boundary as for the seven task kinds the census already knows.

---

## 1. The change, exactly

One `elif` arm added to `_transaction_findings`'s task-kind chain in
`src/deepreason/verification/report.py`, immediately before the closing `else`
at line 972, plus three constants beside the function's existing lazy imports
(lines 720-722). Proposed text, verbatim, so the grant is over the code and not
over a description of it:

    # beside the existing lazy imports at the top of _transaction_findings
    from deepreason.llm.contracts import DefenderOutput, JudgeRuling, VariatorOutput
    from deepreason.llm.wire import AliasTable, wire_contract_for
    from deepreason.run_manifest import resolve_route_seat_base_profile

    # The trial writes ONE task kind for two payload schemas: informal/
    # trial.py's own steps and measures/hv.py's variation sampler, which
    # reaches the same bracket through v6_transactional_phase_call.
    trial_schemas = {"defended-trial-step.v1", "hv-variation-step.v1"}
    trial_models = {
        "defender": DefenderOutput,
        "judge": JudgeRuling,
        "variator": VariatorOutput,
    }
    trial_aliases = AliasTable({"K_001": "placeholder"})

    # ... and the arm itself, before the closing else:
    elif task == "defended_trial_step":
        # The manifest grants these three roles their trial contracts
        # exactly when criticism_policy.authority == "defended_trial"
        # (run_manifest.py::_route_seat_behavioral_contract_assignments),
        # so that is the authority read here. The contract is re-derived
        # through the same wire_contract_for the grant uses rather than
        # named as a literal: a route seat's own presentation profile, not
        # the manifest-wide default, decides between the direct and compact
        # shapes.
        policy = manifest.criticism_policy
        schema = payload.get("schema") if payload is not None else None
        declared = payload.get("role") if payload is not None else None
        if schema not in trial_schemas:
            differences.append("defended trial work has no recognized trial task")
        elif policy is None or policy.authority != "defended_trial":
            differences.append("defended trial work is not authorized by the manifest")
        elif declared not in trial_models:
            differences.append("defended trial work names a role the trial cannot seat")
        else:
            expected_role = declared
            if declared == lease.role and route is not None:
                try:
                    expected_contract = wire_contract_for(
                        declared,
                        trial_models[declared],
                        resolve_route_seat_base_profile(
                            manifest,
                            role=declared,
                            seat=lease.seat,
                            endpoint_id=lease.endpoint_id,
                        ),
                        trial_aliases,
                    ).contract_id
                except ValueError as error:
                    differences.append(str(error))

The arm sets `expected_role` and `expected_contract` and lets the chain's
shared tail (report.py:974-989) do the comparing, which is how every sibling
arm works. `expected_seat` and `expected_endpoint` stay unset deliberately: the
judge ensemble's seats are legitimately 0..n, and a seat outside the frozen
roster is already reported by the route check above the chain
("route judge[5] is absent from the frozen manifest").

**Nothing else moves.** No record format, no field, no check name, no
`_EPISTEMIC_CHECKS` entry, no channel, no digest input, no writer.
`invariants.py` is not opened.

## 2. What "authorised" means for a trial step, and what a forged one looks like

A defended-trial step is authorised when all four hold:

1. **The run's criticism policy authorises a trial at all** —
   `manifest.criticism_policy.authority == "defended_trial"`. This is not a
   choice of predicate; it is the SAME condition
   `_route_seat_behavioral_contract_assignments` uses to grant the three trial
   roles their contracts in the first place (run_manifest.py:2058-2064). Read
   any other condition and the census would disagree with the manifest that
   compiled the run.
2. **The work declares a trial task** — the payload's `schema` is one of the
   two the single writer emits.
3. **The declared role is a trial role, and it is the role the route lease
   actually ran on.** A step cannot claim to be a defender's answer while
   spending a judge seat's tokens.
4. **The contract is the one that role's seat was frozen to render** —
   re-derived, not looked up, through the same `wire_contract_for` the
   manifest's own grant uses.

A **forged** trial step is any preparation carrying
`task_kind=defended_trial_step` that fails one of those. Concretely, the four
shapes the mutation tests must keep reporting:

  - a trial step on a run whose `criticism_policy` is `observe_only` or absent
    — a trial that was never authorised, claiming it was;
  - a trial step whose payload names `judge` while its route lease is
    `defender` — borrowed authority, the cheapest forgery there is;
  - a trial step whose payload names a role outside the three
    (e.g. `conjecturer`) — a call dressed as a trial to reach a seat the trial
    grant covers;
  - a trial step whose `contract_id` is any other contract, including one the
    same seat legitimately holds for something else (`judge[0]` also carries
    `groundingverdictwirev1.direct.v1`).

And, unchanged: a preparation whose `task_kind` is not a member of
`WorkflowTaskKind` at all still falls to the `else` and reports exactly as it
does today. The arm is added before that `else`, never in place of it.

## 3. Blast radius — the gate's own output, and a gap in it I must disclose

`tools/blast_radius.py` on the target file returns, verbatim
(`proof/BLAST_RADIUS.txt`):

    "frozen_surface_contacts": [],
    "frozen_adjacent_contacts": [],
    "reachability": [{"symbol": "_transaction_findings",
                      "status_current": "REACHABLE", ...}],
    "frozen_surface_verdict": "CLEAR",
    "disclosure_summary": "This change touches none of the five frozen
      surfaces. 2 test file(s) and 2 map document(s) assert on the touched
      targets today. ..."

**Do not read that CLEAR as "no grant needed."** It is wrong here, and the
reason is a gap in the instrument, not a property of the change.
`tools/blast_radius.py`'s `FROZEN_SURFACES` registry (lines 110-132) spells
surface 3 as the single path `src/deepreason/invariants.py`. The owning
document spells it "Replay-validation record formats — `invariants.py`,
`verification/`" (`DR-INV-frozen-surfaces` §3), and CLAUDE.md's third-lane
section states the same count explicitly: five surfaces spanning seven paths,
"because surface 3 covers both `invariants.py` and `verification/`". So
`src/deepreason/verification/` is inside a frozen surface and outside the
gate's registry, and every change to it computes CLEAR. Verified as a registry
gap rather than a semantic verdict by a control run naming the five registry
paths directly, which returns all five as `DIRECT` contacts
(`proof/BLAST_RADIUS.txt`, second command). Parked as P2 for its own tranche;
this FIX proceeds as CONTACT on the owning document's word, which outranks the
tool's.

Consumers the gate does report, disposed one by one:

  - `tests/test_v6_verification_transactions.py` (6 hits) — the census's own
    tests. Every one of them uses `task_kind.value` of `"criticism"` or
    `"conjecture"`; none constructs a trial step; none asserts on the `else`
    arm's text. They must keep passing unchanged, and are the check that the
    added arm changed nothing for the seven kinds already known.
  - `tests/test_wire_contract_id_map.py:156` — names the module, not this
    function.
  - `docs/map/SUB-verification.md` lines 65/144/369 and
    `docs/map/INV-frozen-surfaces.md` lines 128/158/248 — the map documents
    that will carry the grant and the `Traps` entry (§5).
  - `qualification_digest: []`, `wheel_smoke_pins: []` — nothing.

## 4. The roads, priced

**Road A — re-derive the contract (RECOMMENDED).** The text in §1. ~40
insertions in one file, zero deletions.
*Strength:* catches all four forgeries in §2, including a contract swap within
one seat's own frozen set.
*Risk, and it is measured rather than argued:* the derivation must reproduce
what the live call recorded, or the fix invents findings on committed roots.
Tested before proposing, over every trial step in every committed root: the
derivation reproduces the recorded `contract_id` on **721 of 721** steps, 0
mismatches (`proof/CONTRACT_DERIVATION_PROOF.txt`). The alias table is a
placeholder and that is safe for the same measured reason — the live calls pass
real aliases and all 721 still match.

**Road B — accept any contract the seat's frozen behavioral plan grants.**
~25 insertions; asks `resolve_route_seat_behavioral_capability` whether the
contract is in the seat's granted set.
*Weaker:* a `judge` trial step naming `groundingverdictwirev1.direct.v1` would
pass. Worse, it is nearly redundant: `workflow/replay.py:2393` already runs
`_validate_preparation_behavioral_authority` over every durable preparation, so
this road adds a security finding for a condition replay has already refused —
it would clear the 75 while adding almost no tripwire of its own.

**Road C — accept the kind whenever the policy authorises a trial.** ~6
insertions. This is the road the parked entry names and rejects: "A change that
only silences the 75 is worse than the defect." Priced only so the operator can
see what the cheap version buys — nothing.

**Road D — do nothing.** Costs: every defended-trial run reports `valid: false`
forever, so `deepreason results --verify` cannot distinguish a tampered record
from an ordinary one on any run that tried a case; and the security channel's
signal-to-noise on the live root is 1 real finding in 76. The 2026-08-29 law
makes tampering-that-buys-a-resumable-run a security boundary, and a boundary
that fires on every run is not a boundary.

Recommendation: **Road A.**

## 5. Change sites (exhaustive, if the grant is given)

  - `src/deepreason/verification/report.py:720-722, 971` — the three constants
    beside the lazy imports and the one `elif` arm. ~40 insertions, 0
    deletions. **FROZEN SURFACE 3 — needs the grant.**
  - `tests/test_defended_trial_transaction_authority.py` — NEW. The
    authorised-step test plus one test per forgery in §2, plus the
    unknown-kind test that pins today's behaviour for a kind outside
    `WorkflowTaskKind`. Built on a real compiled manifest (the stub's shape),
    because the derivation needs one. ~140 lines.
  - `docs/map/INV-frozen-surfaces.md` — the dated "Granted contact" entry the
    brief requires, under surface 3, with a `check:` that goes RED if a trial
    step is again reported unknown. ~40 lines.
  - `docs/map/SUB-verification.md` — one `Traps` entry naming both run ids
    (the live `run-02818acc38961781e2e820d0d6b591fb` and the stub), never
    deleted, per SCHEMA.md. ~12 lines.

Estimated diff: **~40 lines of production code in 1 file**; ~190 lines of
tests and map documents beside it. GOAL.md's "<=150 changed lines" was written
about the fix and holds for it with room to spare; the tests and the map entry
are what this tranche's own brief requires and are counted here separately
rather than squeezed under that ceiling. Correcting my own GOAL line, not
asking for a wider fix.

## 6. THE STOP — frozen-surface grant request

**What I am asking for, in one sentence:** permission to add one `elif` arm and
three constants to `src/deepreason/verification/report.py`, which is inside
frozen surface 3, so that a defended-trial step is measured against the
authority the manifest already froze for it instead of being reported as work
of an unknown kind.

**Why it needs your words rather than my judgement:** surface 3 is frozen, and
this is a WIDENING — a check that will stop reporting something. The document's
own rule for that is that the check must be shown still to report the thing it
was for, which §2 states and the mutation tests in §5 will prove.

**What moves:** one file, ~40 insertions, zero deletions. No record format, no
check name, no `_EPISTEMIC_CHECKS` entry, no channel, no digest input, no
writer, no `invariants.py`.

**What it does to already-committed evidence, measured not asserted:** across
the five committed roots that carry the kind, 721 trial steps in five shapes;
the criticism policy is `defended_trial` on all five; the payload's declared
role equals the route lease's role on all 721; and the proposed derivation
reproduces the recorded contract on all 721. So every root's
`transaction-authority` finding count drops by exactly its trial-step count and
by nothing else; no root gains a finding; and no root is edited. Verified by
re-running the report over the committed bytes before and after
(`proof/COMMITTED_ROOT_CENSUS_before.txt`, and its `_after` twin once the code
exists).

**The instrument's own disclosure is in §3, including the reason its `CLEAR`
verdict must not be taken at face value here.**

**What I recommend:** Road A. **This is your decision.**

If you grant it, your words go into this file verbatim and into
`docs/map/INV-frozen-surfaces.md` as a dated "Granted contact" entry in the
same commit as the code, with a `check:` that goes red if a trial step is again
reported unknown — as the brief instructs.

## 7. Existing tests at risk

  - `tests/test_v6_verification_transactions.py` — MUST KEEP PASSING
    unchanged. No fixture in it constructs a `defended_trial_step`; grepped,
    not assumed.
  - `tests/test_v6_defended_trial_transaction_wiring.py`,
    `tests/test_hv_v6_reachability.py`, `tests/test_judge_canary_dispatch.py`
    — the only other tests naming the kind. All three assert on what the
    WRITER records; none reads the verification report. No fixture depended on
    the defective behaviour, so nothing is updated to accommodate the fix.

## 8. Explicitly not changed

  - **`invariants.py` and `verify_root`.** It already returns zero violations
    on both roots. Nothing there is wrong.
  - **The writer.** `informal/trial.py` records correctly; §2's four criteria
    are read off what it already writes.
  - **The continuation gate.** Today `terminal.continuation_authority` is true
    on a record the report calls invalid. VERIFY.md will state what this fix
    does to that disagreement; changing the gate is PARKED (P1) and is an
    operator decision, not a defect fix.
  - **`tools/blast_radius.py`'s registry**, though §3 shows it is missing
    `verification/`. Fixing an instrument mid-defect is the cross-routing the
    orchestrator forbids. PARKED (P2).
  - **The open-work-order policy question**, parked elsewhere and left there.
