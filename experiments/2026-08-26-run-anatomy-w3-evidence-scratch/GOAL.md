# Goal: census what a run's bound evidence and its scratchpad were actually USED for, versus merely carried
Class: capability-gap

Observed:
    Nothing is broken. Two facts about DeepReason runs are recorded but have
    never been measured. (1) P-R1
    (`experiments/2026-08-25-poietics-program/run`, run id
    `1b31f0065687bd24f64bb08acae1245446b4b31c31b90b141ff95cd5759c9a97`)
    carries 237 typed citation Measure events over a 12-source, 623-block
    dossier, and its RESULTS.md residue R3 states 212 verified citations of
    which only 2 are critic-side — but no instrument reports WHICH bound
    documents and WHICH sections were cited, nor which were never cited at
    all. (2) 41 of the 64 committed run roots emit `Scratch` events
    (P-R1: 17), and no instrument reports when the scratchpad was called,
    why, or whether anything written there ever reached a later candidate
    or criticism. The `presence-is-not-use` question is open in both halves.

Map ids resolved (CLAUDE.md MAP PREFLIGHT):
    DR-SUB-evidence            dossiers, admission blocks, byte-checked
                               citations (`evidence/citations.py`,
                               `evidence/dossier.py`, `evidence/render.py`)
    DR-SUB-scratch             the scratchpad: blocks, links, attention,
                               render receipts (`src/deepreason/scratch/`)
    DR-SEAM-rules-x-scratch    conj gets a bounded single-use view;
                               criticism receives none of it, STRUCTURALLY
    DR-SEAM-schools-x-scratch  a school hands the scratchpad only its bare id
    DR-SEAM-scratch-x-workflow a scratch note is never authority; every
                               mutation is its own log entry with an empty
                               formal `state_diff`
    DR-CON-packs-and-token-economy   what a rendered scratch pack costs
    DR-INV-frozen-surfaces     read; this tranche writes no code, so no
                               frozen surface is approached.

    MAP FINDING (recorded, not fixed here): `DR-SUB-evidence` declares
    `Seams:` EMPTY and `Seams-undocumented: evidence x rules, evidence x
    workflow, evidence x amendment`. The evidence-to-rules seam — the exact
    seam this census measures, where `rules/conj.py` files
    `evidence-citation:` and `rules/crit.py` files `premise-citation:` — has
    no map document. Parked, not authored here.

Success criterion (machine-decidable):
    (a) python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/evidence_census.py
        exits 0 and writes evidence_census.json carrying, for the
        dossier-bound roots: per-source and per-block citation counts split
        by seat role and cycle, the never-cited set, verified-vs-unverified
        outcome codes, and the citing-vs-non-citing artifact survival split.
    (b) python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/scratch_census.py
        exits 0 and writes scratch_census.json carrying, for every root with
        >=1 Scratch event: per-event cycle, seat, preceding event rule,
        typed purpose field where present, the consumption verdict
        (USED / NOT-CONSULTED / UNDECIDABLE) per root, and render-receipt
        token cost where a receipt exists.
    (c) git diff --stat origin/main -- src/ tests/
        prints nothing (read-only gate).

In scope: `experiments/2026-08-26-run-anatomy-w3-evidence-scratch/` (this
    tranche's own directory only); READ-ONLY reads of committed run roots
    under `experiments/`; READ-ONLY reads of `src/deepreason/evidence/` and
    `src/deepreason/scratch/` to learn the typed field names the census must
    read.

NOT in scope: fixing anything the census finds. Defects become PARKED.md
    entries with ready-to-send prompts. Specifically NOT in scope: the
    critic-side citation floor (P-R1 residue R3), the import-role survivor
    inflation (residue R1, already fixed elsewhere), and authoring the
    missing `SEAM-evidence-x-rules.md` map document.

Budget: 0 changed lines under src/ or tests/; census scripts + artifacts
    only; commit and push at every phase boundary.
Stop conditions inherited from orchestrator: yes
