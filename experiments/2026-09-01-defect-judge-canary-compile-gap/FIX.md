# Fix disposition: shared derivation selected, PRICED STOP before implementation

Date: 2026-09-01

Status: **STOPPED before source, test, map, canary, or live edits.**

The operator clarified the governing behavior after R1: `observe_only` must be
an easily reversible choice, never the compiler's involuntary fallback, and a
configuration coherently requesting defended trial must receive it. That
clarification makes delivery—not disclosure—the acceptance condition.

## Road decision

| Road | Behavior | Price | Disposition |
|---|---|---|---|
| A — disclose | Adds the exact typed consequence notice but knowingly leaves authority at `observe_only` and trial grants empty. | The new notice changes affected manifest bytes; a new notice code would also enter the qualification subject unless frozen surface 5 were edited, which is forbidden. | Rejected. It makes the miscompile louder but violates the corrected maximum-configurability requirement. |
| B — derive | When and only when the caller supplies no policy, derives the same configured policy as managed preparation. Explicit policy arguments retain precedence. | Affected defended omissions gain the policy and behavioral grants, moving their manifest and qualification-subject identities. | Semantically selected, but the measurements below trigger the operator's explicit **PRICED STOP**. No implementation authority exists yet. |

If authorized, Road B will centralize the existing managed-path conditional in
one shared `v6_policy.py` helper used by both `preparation.py` and
`compile_run_manifest`. The compiler will call it only for v6, only when the
argument is `None`, and only after routes are resolved, using the actual
argumentative-critic endpoint. The helper must parameterize bindings from the
configured school count rather than blindly assume the public preset's four
schools; otherwise the three-school R1 fixture refuses with
`V4_CRITICISM_SCHOOL_UNKNOWN`. The inline preparation conditional will be
removed, not copied. An explicit `observe_only` policy still wins, the default
legacy configuration still compiles no engaged policy, and no Config default
changes.

## Frozen-surface disposition, recorded before any edit

Forecast contact is exactly surface 4, `src/deepreason/run_manifest.py`, plus
the non-frozen `src/deepreason/v6_policy.py` and
`src/deepreason/preparation.py`. The proposed compiler change alters neither a
Pydantic schema/model, `Literal`, validator, serializer, loader, replay rule,
nor historical manifest. It changes new v6 compilation only. Surface 5
(`qualification.py`) is reached by the changed manifest behavior and will not
be edited. No other frozen or frozen-adjacent surface is contacted.

The pre-edit blast-radius command was:

```text
python tools/blast_radius.py --files src/deepreason/run_manifest.py src/deepreason/v6_policy.py src/deepreason/preparation.py docs/map/SUB-manifest.md docs/map/CON-authority.md docs/map/CON-criticism-source.md experiments/2026-09-01-defect-judge-canary-compile-gap/reproduce_compile_gap.py --symbols compile_run_manifest engaged_criticism_policy build_preparation_manifest --against 3cb51b14e
```

Its material result was:

```json
{
  "frozen_surface_contacts": [
    {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "DIRECT", "target": "src/deepreason/run_manifest.py"},
    {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "SYMBOL_INDIRECT", "target": "compile_run_manifest"}
  ],
  "frozen_adjacent_contacts": [],
  "qualification_digest": [
    {"target": "src/deepreason/run_manifest.py", "tier": "CONFIRMED"},
    {"target": "compile_run_manifest", "tier": "PLAUSIBLE"}
  ],
  "frozen_surface_verdict": "CONTACT"
}
```

The conditional surface-4 grant covers forecast contact discipline; it does
not override the separate digest-price stop. Until the price is explicitly
accepted, the allowed writes end at this tranche's record files. In particular,
there is no edit to `src/`, `tests/`, `docs/map/`, or R3 canary code. If later
authorized, the three owner-map changes and the frozen-surface grant ledger
must move in the same commit as the code and rerunnable checks. Any contact
with another frozen surface remains an immediate stop.

## Digest measurements

Command:

```text
git fetch origin claude/deepreason-p-s1-commitments-wowcib
python experiments/2026-09-01-defect-judge-canary-compile-gap/price_compile_gap.py --expect baseline
```

The probe recompiles each committed defended configuration twice with identical
inputs: once with the policy argument literally omitted and once with the
derived defended policy explicit. The qualification profile digest is
`1e9efe7c053041ede690a4d969c209cea05b65ae8ddfc53ff4cf5a1e2d9bf36a`.
Qualification removes `compiled_at` and `run_input_digest`, so each movement is
behavioral rather than per-run identity noise.

| Case and committed config | Manifest SHA: omitted → derived | Qualification subject: omitted → derived | Source-config hash (unchanged) |
|---|---|---|---|
| P-C1 — `2026-08-25-change-constructive-frontier/run-config.yaml` | `55468838bd863b0c01abde219bbee8af83a8edce13c18bf518c6d0b0ef54a70e` → `d846931857253bacd8d8d88452107dc735159dc0add58c1ec48b16bf4cf2505e` | `f7cfbb9c3dc37375103e0de968f017f8883e5525229c5ce63b8a72e309b5ef38` → `3c3b6f544416319af2dd198206560fff821bdb558cc75f30fafa94a086fe0020` | `331e97ad3b0ee97c1d7b7063ecca7e1b956d7041b98ae98be60b3af39cf722f3` |
| P-R1 — `2026-08-25-poietics-program/run-config.yaml` | `d11bb591ce886b21987004bae071abc4d34e54648d517413eaa34930433ddd6c` → `2e4e1c6b9c53b7f41ae653fd683e2dec449ee016e618c8de7005e5b68dceecba` | `0279485745575ffe9f246421837f630e26f1390c36a70e8ce71548bcc2e0d4d1` → `5ec96a683ba6f3b1523f4a67af53263051add2f4c051542b9346d012b1bb0975` | `0199aed724cad26c3f0fd47a798b57b165a8e5a0e9643f1165ddb69a3a3a7a80` |
| P-C2-H2 — `2026-08-26-pc2-rematch/run-config.yaml` | `bc45e70da8bbbc85d9066df647ebe5278a0afdf6b6cbd489f403b06c9cf8aa18` → `6e9eb44cdd7d248956efc3f90f3d89c1e295b39465c8bd8d27de4dcd4748fe88` | `4c635be9e9ab49cfa4c60c1e76828bbd31d6ed2e3c27cdfc7d9174e5a893f160` → `a55350f4b1e615d91bfb357d75dc928f9d8170fb3e0ba4632d889acb7e0c1d1e` | `331e97ad3b0ee97c1d7b7063ecca7e1b956d7041b98ae98be60b3af39cf722f3` |
| P-C2-H3 — `2026-08-26-pc2-rematch/run-config-h3.yaml` | `cac25ef0515790efa42118df661045512ed0f78667053c30e03dcd5a63503883` → `966048f60d3b76c746105123b495bf97c723e219cdf434ae72f44a6725f1517e` | `6e086c401b2dfb141cf3bbe92eb2753b87ba1c6ff4d2a37cb0a63f4606fb36bd` → `b742f59c55126d382072ea2286eb82eed68663864dd1d4c7e995393c54f2a995` | `c0a727ee010f0460f1d716a523ed4f541596299387ede72dfb6ddd471e6c5e32` |
| split-leg — `2026-08-27-defect-split-leg-recording/run-config.yaml` | `644fd1b1f5d13b23eda64431a5ac647209f26da5447ba5ddbfe6c36dca5df1f4` → `7d724bfbf27e87a40bb4c63c63be1be77a0f8c6caab8eba8edc2f15d6a914f99` | `bd960bc34e6f8a7a53f288c065c34a412a4745435c5bc4be42a01a9fc3a548b2` → `7234a9748f7b731ce17a33661503ba6019856fa49d8f90202022977c1105365e` | `05c32269324ae777e451a8e505124d587cf62bef450d7920e0505bc2cb84ac69` |
| P-C2b — `2026-08-27-pc2b-symmetric-reasoning/run-config.yaml` | `da89d429d9a7715681054051042c8cc52368d015faed964d0cb7aefe09139013` → `752c4ee7ca9119385f9843f7e66e9a737c624105eed62b03ebeef07722ca1e49` | `d6c8597e352d53300cc52e645d0a4c45fb9f5f4841ffa0ebbd569b858b38575d` → `4a1dd1422bb07f0ccdee418f4ae95821a1127e9b6ec4296d3a9f819d162d29be` | `fa7145bd5d9e6cf8a285294213581c8d2f8de9451b81ed7126b99c24d9a1f59b` |
| P-S1 — read-only branch `2026-08-31-p-s1-commitments/run-config.yaml` | `c37a92ad731064bcf17383828533efc1e5058dc24890443e816df45780652d46` → `31216afdae5ae7c3d0eb01377d4fda30c4264f9022f628dc4ed8b271816220fc` | `ac73c37da04364f7e4e63eaa31467e8663d2814d1f6ab6f6ac9ad08b83b2f84b` → `7a1d0a063f359e75ef454e766adaa89c8428e8c15beb865abe46b7c1e8cfd8ba` | `6de55d4fd5800a04377502243b10c61ac12dfd3f1dfad0c369913778f6233951` |

The six main-tree rows are today's hypothetical recompilations of committed
run configurations, not rewrites of their stored roots. Split-leg has no
stored manifest pin. P-S1 is decisive: its omitted result exactly equals the
read-only committed pin `c37a92ad…`, so Road B would give a new compilation of
that same configuration a new manifest and qualification identity. The old
root remains immutable and retains its old verdict; it is never rewritten or
relaunched.

The complete two-judge control fixture independently measured:

| Control | Manifest SHA | Qualification subject |
|---|---|---|
| default explicit observation-only | `de66096f79454255f3b0a4db932186c8573de9000d1ddcc881fc76c6abe45322` | `02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713` |
| defended Config, policy omitted | `a094e56fbedab34509ca070bc71843cb058678f018f0f3a1cab04322263a2fbf` | `c961b331fcf5f3633bba0c42249706747a746069ef53c0b03c1e35607a3ee413` |
| defended Config, explicit `observe_only` override | `2fb3ab698ee6777f038adcb9833fb32b628e1b3ec822946fd34975e162f2c58c` | `c4b7ab8ccb3bd123372d9f434b1788a1d257004c22fbba3a63a82baf99d11ab8` |
| defended Config, explicit defended policy | `0299510d31e292900b36a7d4e20ad9ab9dee9f976a3b9f69b3cca558a3a41fbb` | `de322caa1c8b9d4fefb598bc158ada98376f9f922191409e6168cfc7450057bb` |

An authorized Road B must make the omitted row byte-for-byte equal to the
explicit defended row while leaving both explicit-observation and default
controls pinned.

## Boundary checks and stop

Pre-edit scope remained clean:

```text
git diff --exit-code 3cb51b14e -- src/deepreason tests docs/map
# exit 0
```

The focused baseline pin ring produced two passes and one unrelated pre-edit
environment finding. The default manifest pin and reusable qualification pin
passed. `test_the_shipped_qualification_subject_digest_does_not_move` expected
`83454b08365d…` but this container's untouched anchored tree produced
`8d26382b23cd…`; the qualification payload freezes this container's absolute
Python toolchain path/version digest. No workaround or pin edit was attempted.

Implementation, map movement, R3, full gate, and R4 remain stopped. Resumption
requires an explicit operator decision accepting that future compilations of
the seven defended-plus-omitted configurations receive new manifest and
qualification identities and therefore require qualification for those new
subjects. That acceptance will not authorize rewriting any historical root or
touching any other frozen surface.
