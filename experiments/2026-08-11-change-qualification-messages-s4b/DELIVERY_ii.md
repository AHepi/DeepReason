# Delivered: sub-tranche (ii) — schema-first intake tool (S3)

Branch: `claude/operator-program-seven-items-zpur05` @ `4f5263421`
(pushed, tree clean)

## What changed

A new file, `src/deepreason/intake_form.py`, defines `IntakeFormV1` — a
schema-checked version of the run-application form
(FORM_DR1_RUN_APPLICATION.md) that a caller can validate BEFORE
spending any token. It enforces the three conditions checkable from a
file alone (no conflicting seat bindings, cycles within the ceiling,
token budget within the ceiling), reusing the SAME constants and alias
table the rest of the harness already uses, not re-derived copies.
Two ways to check a file: `deepreason validate-intake FILE` on the
command line, and a `validate_intake` MCP tool for model callers —
both call the identical validator. `FORM_DR1_RUN_APPLICATION.md`'s
Parts A/B1/D are now GENERATED from that same schema
(`tools/render_form_dr1.py`), so the document and the thing that
actually checks a file cannot drift apart the way the old
hand-maintained prose already had (five stale markers).

One real defect was found and fixed during this sub-tranche's own gate
(not shipped, then found later — caught before delivery): the MCP
tool's first draft exposed provider/credential-shaped fields in its
schema, which this codebase's closed MCP facade explicitly forbids
(an endpoint model must never even see that shape). Fixed by giving
the MCP surface a filtered view of the same schema; the command-line
tool, meant for a human or developer, still sees the full one.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R3 | "the form... may not work for smaller models" | done | commit `4f5263421`, VALIDATION_ii.md S3 |
| R4 | "a tool should be the default" — resolved to every caller (Amendment 1: "default for everyone") | done | same |
| R5 | "simple enough for a coding human to fill out and for later documentation" | done | `IntakeFormV1` is a plain file a human can write; FORM_DR1 is its generated documentation |

(R1/R2 were sub-tranche (i)'s, already delivered — see `DELIVERY_i.md`.)

## Assumptions the operator may override

A3: `IntakeFormV1` is standalone, never touching `RunManifest` —
confirmed by an empty frozen-surface diff.
New this sub-tranche: the CLI and MCP paths now validate against two
DIFFERENT schemas (full vs. provider-fields-filtered) even though both
call the same underlying validator — the "one code path" promise holds
for the VALIDATOR, not for the advertised input SHAPE, which differs
by caller for a real safety reason (see above). Flagging this since
the original design didn't anticipate it.

## Map delta

changed: none. created: none (no `docs/map/` document — same reasoning
as sub-tranche (i)). new checks: 0 in the map's own sense; behavior is
proven by `tests/test_intake_form.py` (11 tests) and two real
build-and-install wheel-smoke runs.
left stale: none — `docs_verify --stale` reports 0.

## Errata

errata: none. The MCP credential-exposure issue was caught and fixed
within this sub-tranche's own normal gate discipline (design → build →
regression gate → fix → re-validate) before anything was delivered —
this is the process working as intended, not a committed document or
delivered artifact later found wrong. It is fully recorded in
`CHECKLIST_ii.md`/`VALIDATION_ii.md` for anyone auditing this tranche's
history.

## Parked (not done, not promised)

Two additional pinned MCP tool-name locations
(`tests/test_mcp.py::SUPPORTED_TOOLS`,
`tests/test_mcp_help.py::SUPPORTED_TOOL_NAMES`) exist beyond the two
`scripts/wheel_*.py` pins Item 1's sweep/smoke audit checked (that
audit was correctly scoped to what the task named, not incomplete on
its own terms) — both were found and fixed this sub-tranche because the
full gate caught them, not because anyone went looking. If the
operator wants `tools/root_sweep.py`-style instrument coverage of
test-suite-embedded pins specifically (so a future MCP surface change
is caught before the full gate rather than by it), that is real,
bounded future work, not yet requested.

recommended next: none from this sub-tranche specifically — the
"another window" items (Q3/Q4, now both delivered) close this whole
`change-qualification-messages-s4b` tranche. Residue from sub-tranche
(i) (~528 uncataloged error codes, `PARKED.md` Residue 1) remains the
standing next-step queue for this general area, at the operator's own
pace.

## Tranche close

Both sub-tranches (i) and (ii) are now delivered. REQUEST.md's R1-R5
are all `done`. `experiments/2026-08-11-change-qualification-messages-s4b/`
is closed pending any further operator direction.
