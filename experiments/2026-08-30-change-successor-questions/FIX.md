# FIX — the Q1 granted contact with frozen surface 4, disposed BEFORE the edit

Written at `22ffca6b8`, with the two per-run `Config` fields
and their two `data.pop` lines NOT YET WRITTEN. That ordering is the whole
discipline the five prior surface-4 grants record: the disposition is named
first, then the code is measured against it. A disposition written afterwards
is a description, not a constraint.

## 1. The grant, in the granting party's words

**Q1 GRANTED**, monitor ruling of 2026-08-30, ledgered in CLAUDE.md's P9 law
entry: the frozen-surface-4 grant for the two `Config` fields is granted **per
the documented recipe**. The recipe is the operator's own, stated 2026-08-26
and quoted at `docs/map/INV-frozen-surfaces.md`: *"This is not an exception to
the frozen surface — it is the documented recipe (a Config field is not done
WITHOUT that line; the ENGAGED_CRITICISM_AUTHORITY trap is its ancestor)."*

**Scope, exactly:** two insertions, zero deletions, at exactly four-space
indent, unconditional, inside `_versioned_source_config_data` ONLY. Nothing
else in `src/deepreason/run_manifest.py`. 25 pops -> 27.

Anything beyond that is NOT granted. In particular Q2 Road A — one more line
inside `_CARRIAGE_REQUALIFIES`, also inside this file — is NOT taken; Q2 is
answered ROAD B, which adds nothing here.

## 2. `tools/blast_radius.py`'s own verdict, pasted, and every row disposed

```
$ python tools/blast_radius.py --files src/deepreason/config.py \
      src/deepreason/run_manifest.py \
      --symbols _versioned_source_config_data SUCCESSOR_MINTING_ENABLED \
                SUCCESSOR_QUESTION_DESTINATION

frozen_surface_verdict: CONTACT
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "DIRECT", "target": "src/deepreason/run_manifest.py",
   "detail": "target file is surface path src/deepreason/run_manifest.py"}
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "SYMBOL_INDIRECT", "target": "_versioned_source_config_data",
   "detail": "'_versioned_source_config_data' referenced in
              src/deepreason/run_manifest.py (grep-based; not proof of
              semantic contact)"}
```

| row | disposition |
|---|---|
| DIRECT, `run_manifest.py` is a surface path | **REAL, and it is the granted contact.** Two insertions in one function. No schema, no validator, no Pydantic model, no check name, no record format, no serializer branch. §4's named mistake — "reading the model and not the validator" — cannot arise, because no validator is in the diff. |
| SYMBOL_INDIRECT, `_versioned_source_config_data` | The same contact seen a second time through the tool's grep tier. Not a second surface. |
| `src/deepreason/config.py` | Not a frozen surface, and named in the invocation only because a `Config` field is what CAUSES the surface-4 contact. Two field additions. |

No other surface is reached. Re-derived against all seven paths rather than
recalled — `capabilities/state.py`, `harness.py`, `invariants.py`,
`verification/`, `run_manifest.py`, `qualification.py`, and the
frozen-adjacent `route_fingerprint` in `llm/firewall.py` — and only
`run_manifest.py` appears in the diff.

## 3. What MUST NOT MOVE, with the values measured before the edit

These are the grant's acceptance criteria, and they are the reason the recipe
exists. `Config` is serialized into every manifest's `engine_config_json` and
hashed into `source_config_hash`, both of which the qualification subject
embeds; a new field therefore moves every subject digest and every frozen
manifest golden UNLESS it is dropped here. Measured 2026-08-22 without the
drop: the fixture digest moved `b9038b84…` -> `a5d81e5d…` and the full gate
went red in ~40 places.

Taken at `22ffca6b8`, BEFORE the edit:

```
1. source_config_hash at every schema version
   v1  6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81
   v2  6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81
   v3  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
   v4  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
   v5  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
   v6  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5

2. the shipped qualification subject digest over the committed fixture
   02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713

3. unconditional four-space data.pop count in run_manifest.py
25

4. the fields Config carries today with SUCCESSOR in the name
   none
```

Both `source_config_hash` values and the subject digest match the literals
already pinned inside `docs/map/INV-frozen-surfaces.md`, so the baseline is not
this document's word for it.

**PASS is:** all six hashes byte-identical to the above, the subject digest
byte-identical to the above, the pop count exactly 27, and
`git diff --numstat -- src/deepreason/run_manifest.py` exactly `2	0`.

**If the digest moves, this is a STOP** — the tranche reports and re-pins
nothing. A moved digest means the drop did not take, and re-pinning it would
convert a defect into a new baseline, which is the `ENGAGED_CRITICISM_AUTHORITY`
trap (`docs/ERRATA.md` E44) repeated.

## 4. Why the pop must be UNCONDITIONAL and at exactly four spaces

Not style. Recorded 2026-08-26: scoping such a fix to `schema_version < 4`,
reasoning that no pinned-hash test exists above v3, was itself refuted by two
v5 goldens. And a naive `grep -q 'data.pop("X"'` check passes on the one
arrangement it exists to forbid, because an eight-space guard-scoped pop
CONTAINS the four-space string as a substring — proven by mutation (M-B,
`experiments/2026-08-26-change-f1-discharge-criticism-channel/proof/
granted_contact_mutation.txt`) while v6's hash had already moved.

So this tranche's new `check:` compares the line at its EXACT indent through
`inspect.getsource`, exactly as the `DISCHARGE_POLICY` check does, and it is
captured RED under an eight-space guard-scoped mutant before it is written
down (`proof/frozen_grant_check_red.txt`).

## 5. The naming constraint this file imposes on the two field names

`DR-SEAM-manifest-x-schools` holds, with a `check:`, that the words `stance`,
`lineage`, `crossover` and `reseed` never occur in `run_manifest.py` — which
is what keeps the manifest unable to describe what a SCHOOL is. Every `Config`
field is echoed BY NAME inside this file's drop list, so a field name must
satisfy it. `SUCCESSOR_QUESTION_DESTINATION` and `SUCCESSOR_MINTING_ENABLED`
contain none of the four. Checked, not assumed.

## 6. What the grant BUYS — the four spec items it unblocks

S14 (the two `Config` fields), S15 (these two lines), S19 (already landed under
Q5, whose gate-default clause reads the real field once it exists) and S24 (the
sixth grant block in `INV-frozen-surfaces.md`). Behaviourally it converts two
`getattr` defaults into real configuration surface: before the grant a run
could not CHANGE either default, because `Config` forbids extra fields, so
R4's per-run switch and R6's configurable surface did not exist for any real
run — only for a duck-typed stub. Audit finding F16 measured exactly that, and
F12's parked check (`P9B-8`, "every gate row names a real `Config` field")
becomes writable for the first time and lands in the SAME commit as the fields,
as `PARKED.md` requires.

## 7. No committed root changes verdict

Emission of the carriage notice is compile-time only, and this change adds no
emission at all — it adds two drops, which are READ by
`_unconditionally_dropped_config_fields` and change no byte of any stored
manifest. A committed manifest is read (`model_validate_json`), never
recompiled. The root sweep is retired as an instrument (operator ruling
2026-08-22); this categorical argument is what stands in its place, and it is
the same one the 2026-08-28 grant made and the 2026-08-29 grant qualified.
