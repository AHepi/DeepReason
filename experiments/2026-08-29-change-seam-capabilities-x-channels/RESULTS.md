# RESULTS — DR-SEAM-capabilities-x-channels

Honest ledger. What the record shows, and the residue.

---

## 2026-08-29 — the seam, written

**Delivered.** `docs/map/SEAM-capabilities-x-channels.md` exists, with ten
checks, all single-line, every one run before it was written down.
`docs/map/INDEX.md` carries the routing row, the seam-matrix row and a
corrected count. Both sides' `Seams:` headers name the document; the channels
side's `Seams-undocumented:` no longer promises it.

### What the seam turned out to be

The pair is a **zero-coupling seam** — the second measured instance of the
shape `DR-SEAM-llm-x-verification` records. Counted the way `INDEX.md` counts
(directed `deepreason.*` imports between the two `Owns:` sets, summed both
ways):

    capabilities -> channels : 0
    channels -> capabilities : 0
    total                    : 0

So the pair could never have appeared in the seam matrix, which is built from
that metric. It was invisible to the instrument, not unimportant.

The agreement is that **the channel decides at compile time and the capability
obeys at run time**. `v6_policy.engaged_research_policy` and
`engaged_simulation_policy` are the only code that speaks both vocabularies:
they consult `channels.enabled` and return `ResearchCapabilityPolicyV1` /
`SimulationCapabilityPolicyV1`, types owned by `capabilities/policy.py`. What
crosses is a compiled, frozen policy object — never a flag.

### The finding that made the document worth writing

`CHANNELS_DISABLED` is popped out of the manifest's Config echo by
`run_manifest.py::_versioned_source_config_data` — the SAME function, in the
SAME list, as the five switches audit finding F-A measured being silently
reverted on a `--run-manifest` launch (`JUDGE_SEATS_ENABLED`,
`ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `ENGAGED_CRITICISM_AUTHORITY`,
`LEGACY_CRITICISM_ENABLED`, `SCHOOL_SEATS_ENABLED`).

The channel decision survives that drop. Measured, both halves at once:

    manifest research enabled  : False
    manifest simulation enabled: True
    CHANNELS_DISABLED in echo  : absent
    rebuilt Config.CHANNELS_DISABLED : ()

The rebuilt Config HAS lost the toggle. The compiled policy has NOT lost the
decision. **And the reason is structural rather than lucky:** the capability
side reads no configuration at all — `capabilities/` imports neither
`deepreason.channels` nor `deepreason.config`, and both controllers take
`(harness, manifest)` and lift their policy off
`manifest.inquiry_capability_policy`.

That is now the seam's load-bearing sentence and its first check. A future
change that gave a controller a `Config` — for one convenience knob — would
reopen F-A's failure mode on the evidence channels, and before this document
no existing test would have named it.

### What was checked, and what was only stated

Ten checks, all single-line, all parsed and run. **Three** were demonstrated RED
under deliberate mutation and GREEN again after restore
(`proof/mutation_proof.txt`), with `git status src/` clean at the end:

| Mutation (working tree only, reverted) | Check | Result |
|---|---|---|
| `capabilities/simulation.py` acquires a `Config` import | no-Config-read | RED |
| `engaged_research_policy` stops consulting the channel | manifest-echo differential | RED |
| the severed-road notice stops being channel-gated | notice differential | RED |

The first of those is not a contrived mutation: it is exactly the regression
the document warns about in prose, so the tripwire is proven against the
scenario it was written for.

Gate (`proof/gate_evidence.txt`): `docs_verify` at the 4-failure baseline;
`--links` 0 dangling references over 70 documents; `--audit` 0 findings, so no
check here is refused as unfailable; `--coverage` sweeps this seam with 0
findings.

Unbacked by construction, and left unbacked rather than dressed up: why the
compile-time freeze is the right design, and the reading of F-A as a class
rather than an incident. `SCHEMA.md` says roughly nine in ten prose lines carry
no check and that this is structural; these are among them.

### Residue — what remains unproven

1. **The four-epoch figure is second-hand.** Both `INV-evidence-channels.md`
   and the execution-safety PARKED.md P3 cite commit `74d9f71ca` on branch
   `claude/spec-to-code-technique-k5209o` as the live record of the severed
   simulation road. That commit is unreachable from this worktree
   (`git cat-file -t 74d9f71ca` → `Not a valid object name`), and
   `experiments/2026-08-27-change-technique-run/` does not exist here. Nobody
   reading the main line can open the root behind the claim. The seam document
   says so in its Traps rather than implying a root it could re-read.

2. **The `SIMULATION_RUNNER_UNAVAILABLE` differential is forced, not
   natural.** This host permits user namespaces
   (`sandbox_os.network_denial_available()` → True), so the severed-road notice
   cannot fire here on its own. The check monkeypatches that probe to False to
   produce the two arms. The gating logic is therefore proven; the host
   behaviour it gates on is not exercised.

3. **The `Sweep:` header is declared but its coverage sweep is not part of the
   default gate.** `docs_verify --coverage` is a separate mode. The header was
   run once and is recorded in `proof/`, but nothing fails if a future
   enforcement site becomes invisible to this document.

4. **This tranche wrote no code and proved no behaviour change.** It is a map
   document. Everything it asserts about the code was true before it was
   written; the contribution is that those facts are now re-derivable by
   command instead of by reading two subsystems.

### Found on the way, not fixed — see PARKED.md

- **P1 (HIGH).** 72 `check:` lines across 27 map documents NEVER RUN:
  `docs_verify.py`'s `_CHECK` regex is matched per line, so every multi-line
  `check: python -c "` ... `"` block parses as zero checks. `INV-frozen-
  surfaces.md` heads the list with 10 — ten of the claims authenticating this
  repository's frozen-surface grants are not being re-derived by the instrument
  that reports itself green. Census: `proof/parse_census.txt`.
- **P2 (LOW).** `SUB-capabilities.md`'s body Seams table still calls this pair
  undocumented; only its header line was in this lane's cone.
- **P3 (LOW).** `INV-evidence-channels.md`'s severed-road Trap is still in the
  present tense and does not record the 2026-08-28 fix.
- **P4 (MEDIUM).** `SUB-application.md:403` runs two whole test files, 155s
  idle against a 300s budget, and TIMED OUT under this batch's concurrent load
  — putting `docs_verify` at 5 failed for no code reason. Re-measured idle it
  passes. Cost: 2m36s to disprove.

---

## 2026-08-29 — the correction pass, after adversarial verification

**What happened.** Before this tranche reached the session branch, an
independent adversarial verifier ran a mutation lens and a discipline lens over
the delivered document and FALSIFIED SIX of its claims, plus two bookkeeping
defects. It was right on all eight; every one was re-derived here before being
acted on, and none of the re-derivations contradicted it. The document as
delivered would have shipped two outright false sentences and three claims of
protection it did not have. That is worse than shipping no document, because a
map document is authenticated by re-derivation and these claims read as
authenticated.

### What was falsified, and what was done about it

| # | The claim as delivered | Verdict | What it is now |
|---|---|---|---|
| 1 | "`disabled_channels()` and `unknown_channel_notices()` serve reporting and compile notices" | FALSE | Neither has ANY production caller: repo-wide the names appear once as a docstring line in `v6_policy.py` and otherwise only in two test files. Corrected in the body, with a check (`no-production-caller`) that reddens on a new caller AND on a deleted `channels.py` |
| 2 | PARKED P1: the five unrun checks in `INV-evidence-channels.md` include "the registry's own membership check" | FALSE | That check is line 40, single-line, and RUNS. The five that never run are lines 55, 72, 89, 107, 124; PARKED.md now names them by line and by claim. The headline census (10/5/5, and 72 across 27 documents) was exact and stands |
| 3 | "The first check in this document is what goes red" if a controller acquires a `Config` | OVERCLAIM | The import check pins ARROWS only. An INDIRECT read — a controller importing `deepreason.v6_policy` and recompiling its own policy — left every check green while the manifest said `research.enabled=False` and the controller said `True` with a budget of 6. A new identity check now demands the controller's policy BE the manifest's compiled object; it reddens on that mutation |
| 4 | The Traps check pins the four-epoch runner-profile trap | OVERCLAIM | It was strings-only. Deleting the guard reddened it; INVERTING it (`!= container` → `!= declarative`, the same defect pointed the other way) did not, because both strings survive elsewhere in `execute`. It now pins the guard's AST — comparisons, operators, literals and reason code together — and reddens on both |
| 5 | `--coverage: 0 findings` as gate evidence that the seam names every enforcement site | VACUOUS | Recomputed by hand: three candidate files, ZERO enforcement sites, because the channel decision is consumed by a boolean guard and `--coverage` only sees comparisons and raises. A zero that cannot be non-zero is not evidence. The `Sweep:` header is REMOVED with the reason stated in the body, and replaced by a reader census that can fail |
| 6 | The F-A framing of the engine-config echo drop | STALE | The P10 fix `a40450f1c` is in this tree and now types the drop as `ENGINE_CONFIG_FIELD_NOT_CARRIED` at `/engine_config/CHANNELS_DISABLED`. Both the body section and the Traps entry say so, with a check |
| 7 | `proof/cone.txt` records the tranche's cone | INCOMPLETE | It listed 7 paths; the diff had 12. Regenerated |
| 8 | `SUB-capabilities.md` header says documented, body table says undocumented | CONTRADICTION | Fixed, and the cone widened by one file to allow it. PARKED P2 is CLOSED, with the ratchet its own prompt asked for: a check that every body row appears in exactly one header and every header entry appears as a row |

### One thing the verifier did not find, discovered while fixing #1

Correcting #1 collapsed the fourth Trap. It told the reader to "read the compile
notices, not the policy, to learn" whether a channel is off by intent or by
typo. Since `unknown_channel_notices` has no production caller, a compile never
emits `CHANNEL_UNKNOWN`. Measured: `channels_disabled=("reserch",)` compiles a
manifest whose ONLY notice is the P10 field-not-carried one, with research still
ENABLED. The advice was false and is withdrawn; the entry now says what a reader
can actually do, and carries a check that reddens if the registry stops typing
the distinction or if someone wires it into the compile.

### Checks: 10 → 15 on the seam, 17 → 18 on the subsystem

Five added, one strengthened in place, none deleted and none weakened. Every one
is single-line, parses under `docs_verify`'s own `_CHECK` regex, and was proven
RED under a deliberate mutation and GREEN after restore before it was written
down. Twelve mutations, full transcript in `proof/correction_mutation_proof.txt`,
run on an isolated byte-copy of the tree so the lane worktree was never wrong
(`SCHEMA.md`: "run a falsification pass, or measure the tree, never both at
once"). The transcript deliberately records two GREEN results as well — the
import check under the indirect read, and the old strings-only check under the
inversion — because those are the falsifications, and a proof file that only
shows reds hides what was wrong.

### Residue — what remains unproven

Superseding residue items 3 and 4 of the segment above; items 1 and 2 stand.

1. **The identity tripwire does not make a `Config` unreachable.**
   `capabilities/audit.py` already imports `deepreason.run_manifest`, which
   exports `config_from_run_manifest`. A controller reading configuration
   through an already-permitted module would pass both of this document's
   checks. The behavioural authority there is the capability test suite —
   measured, `tests/test_research_capability.py` returns `7 failed, 4 passed`
   under the indirect-read mutation — and the document now says so rather than
   letting a map check stand in for a gate.
2. **The completeness census is an import census, not a use census.** It proves
   exactly one module reaches `deepreason.channels`. It would not catch a
   channel decision smuggled across as a plain bool through some other module's
   signature. Nothing measured suggests that exists today; nothing here rules
   it out either.
3. **`--coverage` is now structurally silent for this seam by construction.**
   Removing the header is the honest move and `SCHEMA.md` prescribes it for the
   neighbouring case, but it does mean this document has no mechanical
   completeness sweep — only the hand census. If the channel decision ever
   becomes a comparison or a raise, the header should come back.
4. **This pass still wrote no code and proved no behaviour change.** It made a
   map document stop claiming things that are not true, and made three of its
   claims enforceable that were not. Everything it asserts about the code was
   true before it was written.
5. **Not re-run here, by instruction:** the full pytest gate and the full
   `docs_verify` sweep. This pass changed no `src/` file; the orchestrator
   re-measures both at fan-in against the stated 4-failure baseline.
6. **`SUB-capabilities.md` still carries one check line that never runs**
   (PARKED P1). It was left alone deliberately: P1 is a repo-wide decision
   about the parser, another window was reported to be landing it, and
   rewriting one check here would collide with that and shift the census this
   tranche just corrected.

**Accepted does not mean true.** Six claims in this document passed a lane's own
review, its own ten green checks, and a green gate, and were false or hollow
anyway. What caught them was a reader with no stake in the tranche and a licence
to mutate the tree.
