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

### Fourth measurement — 2026-08-16, fresh container, reproduced by construction

The close-out session ran on a container cloned fresh from
`origin/claude/calculus-rung2-step2-premise-pes36e`, with no build state, no
prior test run, and no working-tree edits. This removes the environment as a
variable entirely, and it settles the one hypothesis the first three
measurements could not fully kill from inside a single container.

| Tree state | Result | Wall time |
|---|---|---|
| as committed | **4 passed** | 19.7 s |
| `docs/map/SUB-adjudication.md` + one comment line | **2 failed, 2 passed** | 7.9 s |

The failing pair is exactly `test_run_identity_is_deterministic_through_the_one_road`
and `test_the_grounded_tranche_config_enters_through_the_new_door`, and the sha
moves `8e22d043...` → `711e3f31...` for one appended HTML comment. The probe
file was reverted immediately; the tree is clean.

Two things this fixes in the record:

- **The environmental hypothesis is dead.** A one-line edit to a map document
  reproduces both failures on a machine that has never built anything before,
  so nothing about a stale container was ever required to explain them.
- **`first == second` still held in the failing run** — the intra-run
  determinism assert passes and only the PIN assert fails. A cache whose key
  omitted builder identity cannot produce that pattern. Refuted for the second
  time, now on clean ground.

The 7.9 s-vs-19.7 s timing reproduces the "0.5 s vs 9.5 s" signal that
originally suggested caching, and confirms its real cause: the failing run
short-circuits at an early assert and never reaches the second build, so the
faster run is the one doing LESS work, not the one skipping a rebuild.

**The defect is unchanged and still parked.** What moved is its evidence: the
coupling is now demonstrated on demand rather than inferred from a tranche's
incidental edits, so whoever picks this up can reproduce it in 30 seconds with
one appended line.

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

Reproduce it yourself in 30 seconds, on any tree, no build state needed:

    printf '\n<!-- probe -->\n' >> docs/map/SUB-adjudication.md
    python -m pytest tests/test_single_run_path.py -q -k "manifest or run_identity"
    git checkout -- docs/map/SUB-adjudication.md

Confirmed 2026-08-16 on a fresh container: green as committed (4 passed, 19.7s),
both tests red with one appended comment line (2 failed, 7.9s, sha 8e22d043... ->
711e3f31...). The environment is NOT a variable, and the intra-run determinism
assert passes in the failing run -- so a cache-key hypothesis is refuted, twice.

Roads: (a) freeze the dossier by copying those bytes into the tranche directory,
so the fixture pins its own immutable evidence rather than living documentation;
(b) drop the sha pin and assert the weaker property the test actually needs
(two builds agree, and the manifest loads); (c) accept the coupling and add a
loud comment in both map documents. (a) looks right -- an acceptance fixture
should own its inputs -- but measure the alternatives before choosing.
```

### Addendum — 2026-08-16, P1 settled (appended; nothing above is rewritten)

Fixed in `experiments/2026-08-16-defect-manifest-sha-doc-coupling`. Two
corrections to the ready-to-send prompt above, both to its FRAMING, none
to its measurements — the four measurements and the refutation of the
cache hypothesis stand exactly as written.

**1. The verdict was open in the prompt and is now closed: the BUILDER IS
CORRECT.** The prompt describes a "coupling defect", which reads as though
the coupling itself were wrong. It is not. A run that binds documents as
evidence has those documents inside its identity by construction — same
question, same config, DIFFERENT evidence is a different run — and an A/B
probe proved the ingestion is confined to the declared dossier: editing
`docs/map/SUB-adjudication.md` (bound) moved `evidence_dossier_digest`,
`run_input_digest` and `manifest_sha256` together; editing
`docs/map/SUB-scheduler.md` (not bound) moved nothing. The defect was
entirely in the two tests, which pinned a constant against inputs they did
not own.

**2. Road (a) is SUPERSEDED — do not take it.** "Freeze the dossier by
copying those bytes into the tranche directory" would edit
`experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`,
making that committed script disagree with the `evidence-dossier.json` and
`run-manifest.sha256` it actually produced — the live tranche's record of
what that run bound. Road (b) as stated ("drop the sha pin and assert the
weaker property") is also not what shipped, because the property that
shipped is STRONGER, not weaker: the compiled manifest is compared field
by field against the live run's committed `run-manifest.json`, excluding
only `run_input_digest`, so a mismatch names the field that drifted. The
freeze that road (a) wanted lives in the new sensitivity test's `tmp_path`,
where it owns its bytes and rots nothing. Road (c) was never viable — a
loud comment does not stop a gate going red.

The reproduction in the prompt above still works verbatim and now prints
green on both arms; `probe_digests.py` in the fixing tranche is its
committed, self-restoring form.
