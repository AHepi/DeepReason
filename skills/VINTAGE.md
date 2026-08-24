# VINTAGE.md — which treadle release each skill in this directory came from

A SKILL.md does not record its own version, and this directory holds files
from two releases. Update this table whenever a skill is added or replaced.

| skill | vintage | source of truth |
|---|---|---|
| `assembly` | **0.5.0** | `tools/treadle0.5/skills/assembly/` |
| `minimal-pair-review` | **0.5.0** | `tools/treadle0.5/skills/minimal-pair-review/` |
| `review-response` | **0.5.0** (new in 0.5) | `tools/treadle0.5/skills/review-response/` |
| `denotation-tests` | 0.4.1 | `tools/treadle/repo-assets/skills/denotation-tests/` |
| `discharge-typing` | 0.4.1 | `tools/treadle/repo-assets/skills/discharge-typing/` |
| `example-battery` | 0.4.1 | `tools/treadle/repo-assets/skills/example-battery/` |
| `mapping-table` | 0.4.1 | `tools/treadle/repo-assets/skills/mapping-table/` |
| `semantic-round-trip` | 0.4.1 | `tools/treadle/repo-assets/skills/semantic-round-trip/` |
| `term-pinning` | 0.4.1 | `tools/treadle/repo-assets/skills/term-pinning/` |
| `deduction` | 0.4.1 (dropped in 0.5) | `tools/treadle/repo-assets/skills/deduction/` |
| `model-zoo-discipline` | 0.4.1 (dropped in 0.5) | `tools/treadle/repo-assets/skills/model-zoo-discipline/` |
| `refutation-first` | 0.4.1 (dropped in 0.5) | `tools/treadle/repo-assets/skills/refutation-first/` |
| `pilot-task` | DeepReason-authored, 2026-08-23 | this repo (deviation D5) |

The six 0.4.1-vintage skills that 0.5 also ships were NOT upgraded: the
minimal-install rule installs only what an acceptance command names, and none
names them. 0.5's versions are readable at `tools/treadle0.5/skills/` and
differ — see `tools/treadle0.5/README.md`'s change table for what each gained.

`pilot-task` and the frozen 0.4.1 reviewer prompt are what the recorded
pilot ran; see `experiments/2026-08-23-treadle-pilot/pinned/`.
