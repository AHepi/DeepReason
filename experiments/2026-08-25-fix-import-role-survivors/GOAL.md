# Goal: the results surface must not count import-role admission records as survivors

Class: defect

Observed: `deepreason results` reports **82 survivors** for the committed P-R1
root `experiments/2026-08-25-poietics-program/run`
(run `1b31f0065687bd24f64bb08acae1245446b4b31c31b90b141ff95cd5759c9a97`), and
**24 of those 82 are IMPORT-role admission records** — sections of the
operator's attached dossier, auto-accepted at seed and never removed from the
survivor set. Measured from the typed record, not from prose: the root's own
`run-result.json` lists 82 ids, and each id's
`state.artifacts[aid].provenance.role` over the replayed state resolves to
58 `CONJECTURER` + 24 `IMPORT`. CLAUDE.md states the contradicted guarantee
verbatim, in the list whose violations were "real, recorded defects":
*"import-role admission records never count as 'survivors'."* The finding is
already committed as `experiments/2026-08-25-poietics-program/RESULTS.md`
residue **R1** and `PARKED.md` **P4**; this tranche is P4's ready-to-send
prompt executed.

Success criterion (machine-decidable):

    python -m pytest tests/test_import_role_survivors.py -q
    # 0 failed; asserts against the COMMITTED P-R1 root that
    #   deepreason.application.results.results_summary(<P-R1 root>)
    #     ["artifacts"]["survivor_count"] == 58
    #   and that the 24 excluded ids are exactly the IMPORT-role ones,
    #   and that the 26/8 conjecture/import split of the 34 artifacts
    #   passing `poietics-installation-mechanism@v1` is reproduced.

    deepreason results experiments/2026-08-25-poietics-program/run
    # "survivors (positions still standing at the end): 58"

    python -m pytest tests/ -q -n 4
    # 0 failed (baseline re-derived at this tranche's base commit)

    python tools/docs_verify.py
    # no NEW failures against the 3 known pre-existing shallow-clone failures

In scope:
  - `src/deepreason/scheduler/scheduler.py` — where the invariant is ALREADY
    enforced (`_select_problem`, DR-CON-scheduler-ranking) and where
    `run_report` writes the survivor set into `run-result.json`
  - `src/deepreason/application/results.py` — DR-SUB-application, the ONE
    typed-outcome retrieval surface, which today derives the count as
    `len(result["survivors"])`
  - `tests/test_import_role_survivors.py` (new) + the map documents that
    cover both sides, moved in the SAME commit

NOT in scope: `src/deepreason/report.py::eval_report`'s `survivor_hv` /
`survivor_reach` distributions and `src/deepreason/loop.py::run_problem`'s
survivor list. Both derive a survivor set of their own and would, on the
one-authority reading, consume the same predicate — but neither is the
results surface, and on the P-R1 root neither number moves (measured: 0 of
the 24 IMPORT survivors carry an `hv` or a `reach` entry, so the
distributions already exclude them de facto; `loop.py` is the P1 minimal
loop, reachable only from `tests/test_loop.py`). PARKED, not fixed.

Also NOT in scope: the `accepted` count (435 accepted artifacts, of which 36
are IMPORT-role). The invariant names "survivors" and nothing else; widening
it to acceptance would change what an ACCEPTED status means, which is an
authority question, not a reporting one.

Map ids resolved (orchestrator map preflight):
  - `DR-SUB-scheduler` — owns `run_report` and `_select_problem`
  - `DR-CON-scheduler-ranking` — states the invariant and carries its check
  - `DR-SUB-application` — owns `results_summary` / `render_results`
  - `DR-SUB-evidence` — owns the dossier admission that mints IMPORT records
  - `DR-INV-frozen-surfaces` — read BEFORE designing: **none of the five
    frozen surfaces is in scope.** `scheduler/scheduler.py` and
    `application/results.py` are on no frozen list, and no manifest schema,
    qualification subject, capability digest, harness event application or
    replay-validation record format is touched. To be re-confirmed
    mechanically by `tools/blast_radius.py` before any code lands.
  - No `SEAM-application-x-scheduler.md` exists. `DR-INDEX`'s matrix does not
    list the pair at all, yet `application/text_runs.py` already imports
    `run_report` from `scheduler.scheduler`. Recorded as a finding, not a
    blocker.

Budget: <=150 changed lines, phase-boundary commits, ~1 session.
Stop conditions inherited from orchestrator: yes
