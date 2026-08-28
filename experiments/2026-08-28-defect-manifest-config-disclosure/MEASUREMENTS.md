# MEASUREMENTS — what the disclosure costs, measured before it is accepted

All figures re-derivable on this branch. Fixture: `tests/test_reusable_qualification.py::_manifest`
with `_profile()`, `compiled_at="2026-07-23T00:00:00Z"`. Digests are the full
`qualification_subject_digest(manifest, profile)` unless truncated for width.

## The constraint the implementation ran into

`qualification_subject_payload` (`qualification.py:263`) builds its subject from
`manifest.model_dump(mode="json", by_alias=True)`, which includes
`compile_notices`. So a compile notice NAMING a dropped `Config` field puts that
field's name and value INTO the qualification subject — defeating, by way of its
own disclosure, the exclusion three committed tests exist to guarantee:

- `test_adjudication_status_authority_flag_excluded_from_subject_digest` (Part C, S2a/C9)
- `test_judge_seats_fields_excluded_from_subject_digest` (Part D, S2b/C9)
- `test_school_seats_enabled_field_excluded_from_subject_digest` (Part E Step 48, S2d/C3)

Each states the same rule: these knobs gate dispatch, not provider identity, so
they must not cost a home a ~14-minute qualification battery. That rule is right
and this tranche does not weaken it.

## The measurement

| config | base subject digest | A: notice in subject | B-narrow: notice excluded |
|---|---|---|---|
| default | `02ee7e098bb92390` | `02ee7e098bb92390` | `02ee7e098bb92390` |
| `JUDGE_SEATS_ENABLED=True` | `02ee7e098bb92390` | **`478c15619dd81fb4`** | `02ee7e098bb92390` |
| `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True` | `02ee7e098bb92390` | **`230c5dff627a7d37`** | `02ee7e098bb92390` |
| `SCHOOL_SEATS_ENABLED=True` | `02ee7e098bb92390` | **`170fec05dc38d47a`** | `02ee7e098bb92390` |
| P-T1's five switches | `02ee7e098bb92390` | **`f40357e9e31b8768`** | `02ee7e098bb92390` |
| a manifest already carrying `SECOND_JUDGE_FAMILY_REQUIRED` | `061efe5bdf7eb565…` | `061efe5bdf7eb565…` | `061efe5bdf7eb565…` |

`source_config_hash` is byte-identical under every option at every schema
version — `6c2d01f6b8cbe65e…` (v1/v2), `2624603035bc335e…` (v3-v6) — because
the echo itself is untouched. Only the qualification subject was ever at risk.

**Option B-narrow moves ZERO qualification subject digests.** No home
re-qualifies, no committed pin moves, and the three exclusion tests keep their
exact guarantee.

Full-run outputs: `probe/digests_base.txt`, `probe/digests_optionA.txt`,
`probe/digests_optionB.txt`, `probe/digests_optionB_narrow.txt`.

## The three options as they actually price out

**A — leave `qualification.py` alone; let the notice enter the subject.**
Every configuration setting any of the 25 dropped knobs away from default gets
a new subject digest: 7 of the 8 committed `run-config.yaml` files on `main`,
each home paying one ~14-minute, ~1160-call battery. And the three tests above
must be INVERTED to pass — their guarantee deleted, not adjusted. CLAUDE.md:
"Never weaken an assertion to get green." **Rejected on that ground alone.**

**B-narrow — exclude the disclosure notice from the qualification subject.**
Seven inserted lines in `qualification_subject_payload`: notices whose code is
`ENGINE_CONFIG_FIELD_NOT_CARRIED` are dropped from the subject; every other
notice keeps its contribution, so no existing subject moves either. Zero digest
movement, measured above. The rule it encodes is the one the three tests
already encode, carried one step further: *a disclosure that a subject-excluded
Config field was not carried must not itself enter the subject, or the
exclusion is defeated by its own disclosure.*
**Contacts frozen surface 5 (`qualification.py`). NOT GRANTED — this is the STOP.**

**C — print the disclosure at compile time and do not store it.**
Zero digest movement, zero frozen-surface contact, and the reason to reject it:
the disclosure would not be in the record. "The record is the only admissible
evidence" — a warning that exists only in a terminal cannot be read back off a
manifest six weeks later, which is exactly what the P-T1 investigation needed
to do and could not.

## Recommendation

**B-narrow**, and the grant it needs is small: seven inserted lines in one
function, no schema, no validator, no record format, and a measurement showing
zero digest movement rather than an argument that there should be none.
