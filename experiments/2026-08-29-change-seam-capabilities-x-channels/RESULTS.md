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
