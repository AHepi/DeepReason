# Goal: a criticism can declare the artifacts it essentially rests on, so refuting one of them lifts its attack and reinstates its target

Class: defect

Observed: on the installed package at `323fefb53`, the §0 script of
`docs/proposals/OIS_1_1_to_DeepReason_configuration.md` returns

    DEPENDENCE ('refuted', 'suspended_unsupported')
    EVIDENCE   ('accepted', 'refuted')

(reproduced by this window, 2026-09-05, `python -c` against the public
`Harness` API, no run root). The EVIDENCE branch is the documented
behaviour: `docs/map/CON-warrants-and-attacks.md` states "A verdict may
declare what it rests on, and that declaration is the evidence closure's
only entry point", and the evidence closure lifts the attack onto the
criticism's validity node before pass one, reinstating the target. The
DEPENDENCE branch leaves the target `refuted` while the criticism that
attacked it is itself `suspended_unsupported` — a criticism whose ground
has been withdrawn still defeats what it attacked.

Why it is a defect and not merely a missing feature: the evidence closure
is built, documented and tested; what is missing is any PRODUCER for it on
the criticism road. `llm/contracts.py::ArgumentativeCriticOutput` has no
field in which a criticism names the artifacts it essentially relies on
(`premise` is a presupposition of the PROBLEM, not of the criticism), so
the documented branch is unreachable from the wire and no live criticism
can ever take it. The correct pass-2 rule beside it — "refuting a premise
never refutes its dependents: pass 2 gives them `SUSPENDED_UNSUPPORTED`"
— is correct and unchanged; it is about the dependent, not about the
target of an attack the dependent carried.

Success criterion (machine-decidable):

    # 1. the wire road exists and reaches the documented branch
    python experiments/2026-09-05-criticism-premise-declaration/s0_wire.py
    # expected: the §0 DEPENDENCE scenario, rewritten as a critic
    # DECLARING the premise essential through the wire, prints
    #   ('accepted', 'refuted')
    # i.e. the EVIDENCE tuple.

    # 2. regression test on a stub root, mutation-proven
    python -m pytest tests/test_criticism_premises.py -q
    # expected: passed; and removing the ν-registration in rules/crit.py
    # turns it red (mutation recorded in VERIFY.md)

    # 3. no regression
    python -m pytest tests/ -q -n 4
    # expected: 0 failed
    python tools/docs_verify.py
    # expected: 0 failed

    # 4. the stored default critic form is byte-identical when the new
    #    field is absent
    python -m pytest tests/ -q -k "golden or template" 
    # expected: 0 failed, no golden file edited

In scope (map ids resolved from `docs/map/INDEX.md`, seam before subsystems):
  - `DR-SEAM-llm-x-rules` — the wire contract → mint site seam (read first)
  - `DR-CON-criticism-source` — the socket that attacks a target (`rules/crit.py`)
  - `DR-CON-warrants-and-attacks` — the ν / evidence-closure rule this restores;
    owns the map document that gains the Traps entry and the new check
  Supporting, read not owned: `DR-SUB-llm` (`llm/contracts.py`),
  `DR-SUB-evaluation` (`informal/trial.py`), `DR-SEAM-adjudication-x-rules`.

  Paths: `src/deepreason/llm/contracts.py`, `src/deepreason/rules/crit.py`,
  `src/deepreason/informal/trial.py` (+ any other argumentative mint site the
  census in DIAGNOSIS.md finds), `docs/map/CON-warrants-and-attacks.md`.

NOT in scope: `src/deepreason/adjudication/` — the evidence closure already
exists and is the thing being reached, not the thing being changed. If the fix
appears to need an adjudication edit, that is a STOP-and-report condition
(operator's instruction, this window). Also not in scope: every other contract
addition in the source proposal's §4 (`defect`, `standard`, `bearing`,
`discriminator`, `merits_at_stake`, the defender and recorder contracts) — one
tranche, one goal; they are PARKED.

Explicitly NOT adopted from the source document: its rule that "a case with
attack=true and an empty discriminator is a failed call", and any analogous
penalty on an empty premise list. The formalism-optional law binds: the new
field is OPTIONAL, an empty list is exactly today's behaviour, and no
admission, rank, criticism-exposure or acceptance outcome may weigh on whether
it is filled.

Frozen surfaces: forecast NO CONTACT. `tools/blast_radius.py` is run before
any code is written and its verdict pasted into FIX.md; any CONTACT row is a
STOP for an operator grant.

Budget: <=150 changed lines of production code, 1 commit, ~4 hours
Stop conditions inherited from orchestrator: yes
