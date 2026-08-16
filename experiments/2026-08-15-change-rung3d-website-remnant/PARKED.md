# Parked — Rung 3d

## P1 — a map document is an evidence-dossier input to a PINNED manifest golden

**What.** `experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`
digests six files as its evidence dossier, and two of them are MAP documents:

    docs/map/CON-warrants-and-attacks.md
    docs/map/SUB-adjudication.md

The compiled manifest's `sha256` is a content address over those bytes, and
`tests/test_single_run_path.py` pins that sha as `GROUNDED_MANIFEST_SHA256`.
So **any legitimate edit to either map document breaks two run-identity tests**,
with a failure message that names a digest and points at nothing.

**The diagnosis, from three measurements taken while chasing it:**

1. Restoring `SpawnTrigger.SUCCESSOR` fixed four of six failures — those were
   genuinely the enum (pre-v2 roots stop parsing).
2. The two manifest failures survived that restore, so the enum was never
   their cause.
3. Reverting all four source files this tranche touched left both still
   failing — and reverting one MAP file fixed both. The builder was never
   serving a stale artifact: within one run `first == second` always held, so
   it was deterministic throughout. It was recomputing correctly over inputs
   that had changed.

**The cache hypothesis is refuted, and that matters.** A cache whose key omitted
builder identity would have shown non-determinism between two builds in one
process; the test asserts exactly that equality and it passed every time. What
looked like a stale artifact was a correct content address over edited evidence.
The 0.5s-vs-9.5s timing that suggested caching was pytest's own collection
short-circuit on an early assert, not a skipped rebuild.

**Why it is a defect anyway.** Within-version determinism is intact, but the
COUPLING is wrong: the map is documentation that must move whenever code moves
(SCHEMA.md makes that a rule), and a fixture that pins a digest over
documentation makes an ordinary, mandated edit look like a run-identity
regression. Two things that must both be free to change are welded together.

**Not fixed here.** This tranche is the website-remnant removal, shipping alone.

### Ready-to-send prompt

```
Route through deepreason-orchestrator.

DEFECT: a pinned run-identity golden is coupled to map documentation.

experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py
digests six dossier files, two of which are docs/map/CON-warrants-and-attacks.md
and docs/map/SUB-adjudication.md. The compiled manifest sha is a content
address over them, and tests/test_single_run_path.py pins it as
GROUNDED_MANIFEST_SHA256. Editing either map document -- which SCHEMA.md
REQUIRES whenever the code it documents changes -- fails
test_run_identity_is_deterministic_through_the_one_road and
test_the_grounded_tranche_config_enters_through_the_new_door with a digest
mismatch that names no cause.

Reproduced 2026-08-15 (experiments/2026-08-15-change-rung3d-website-remnant):
editing SUB-adjudication.md moved the sha from 8e22d043... to a437a833...;
reverting that one file restored it. Determinism is NOT broken -- two builds in
one process agree every time -- so this is a coupling defect, not a caching one.

Roads: (a) freeze the dossier by copying those bytes into the tranche directory,
so the fixture pins its own immutable evidence rather than living documentation;
(b) drop the sha pin and assert the weaker property the test actually needs
(two builds agree, and the manifest loads); (c) accept the coupling and add a
loud comment in both map documents. (a) looks right -- an acceptance fixture
should own its inputs -- but measure the alternatives before choosing.
```
