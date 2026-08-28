# Wave A incident-derived regression fixtures

These files are **minimized derived reproductions**, not copies of the original
A1, A2, or A3 run roots. The original archive named by the incident review was
not available in this workspace. No original run byte is included or rewritten.

Each descriptor is dependency-complete for the test builder in
`tests/test_incident_wave_a_v2_fixtures.py`. The builder creates a fresh
RunManifest v5 root through public DeepReason APIs and passes that root to the
real `verify_root_report()` adapter.

The descriptors are linked to incident
`DR-2026-07-16-AUTONOMOUS-INQUIRY-WAVE-A` by the SHA-256 of the user-provided
review (`2f086397643e439dd711d656611f943a3edbb3327672faf81f16ea40d6ebf282`)
and by repository head `056af85e4c6018bcdf44e73c2ada78fabccb4a81`.

Limitations are deliberately explicit:

- timings, provider transcripts, complete event prefixes, and original object
  identities cannot be claimed without the archive;
- A2's orphan exposure is reproduced as a canonical v5 dossier receipt bound
  to no durable work order;
- A2's bridge-laundering conclusion is carried by a separately labelled
  derived v2 audit terminal because the archived bridge records are absent;
- A1 and A3 reproduce criticism debt and failed terminals; A3 additionally
  reproduces a canonical simulation proposal that never reaches execution.

The descriptor hashes and generated-root hashes are frozen in
`PROVENANCE.json`. Any intentional fixture change therefore requires an
explicit provenance update.

## Recorded pin moves

`generated_root_sha256` has moved once since it was frozen, and every move is
recorded in `PROVENANCE.json` under `generated_root_sha256_history` with its
before, its after, and its reason:

- **2026-08-28, A3 only** — the render-layout tranche
  (`experiments/2026-08-28-change-render-layout-robust`, R2a) makes a
  conjecturer prompt restate the question last. The prompt blob and the six
  workflow records content-addressed from it therefore carry new ids: 7 of
  A3's 23 files moved. A1 and A2 were byte-identical across the change, and no
  committed run root changed verdict.
