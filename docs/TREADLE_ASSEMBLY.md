# TREADLE_ASSEMBLY.md — what of treadle 0.5.0 is installed here, and why

Written per `tools/treadle0.5/skills/assembly/SKILL.md`, BEFORE anything was
copied, as `SETUP.md` step 2 requires. Vendored source of truth:
`tools/treadle0.5/` (zip sha256
`1818f7b658c1ffbb23fc7d97dacc54fbfddb790851d6489cbc83d56cb5d18741`).

Status: **UNREVIEWED by the owner at write time.** SETUP step 2 says to show
this table to the human owner if one is present and to proceed if not; the
operator supplied the zip and said "keep going", so it proceeds and is marked
unreviewed here rather than silently treated as approved.

Package proven before trusting it (SETUP step 1):

    python3 tools/treadle0.5/selftest.py
    -> 38 checks, 12 planted violations correctly refused, 0 failed (exit 0)

## The three glue questions (MODULES.md), answered in order

**(a) What is "done"?** DeepReason already answers this for its own artifacts,
and those answers are not replaced: `python -m pytest tests/ -q -n 4` (0 failed),
`python tools/docs_verify.py` (every `check:` re-derives its document's claims
against the code), `tools/blast_radius.py`, `tools/diff_budget.py`. treadle 0.5
is installed only where DeepReason has NO deterministic acceptor today. Two
such places, and their commands:

    python3 scripts/consistency_packet.py --verify
    python3 -c "import sys; sys.path.insert(0,'scripts'); from review_harness import verify_ledger; print('rows:', verify_ledger('zoo/reviews/calls.jsonl'))"

**(b) Who must not collide?** One actor, one session, one branch — commit
early by hand. No gate is needed for that, and none is installed from 0.5.
Note for the future: `MODULES.md` records M1 `swarm_gate.py` as lost with the
0.4.1 archive. **It is not lost here** — `tools/treadle/repo-assets/swarm_gate.py`
holds it, and `scripts/swarm_gate.py` is a working install with a
hash-chained board from this tranche's pilot (`swarm_gate.py log-verify` ->
`chain intact`). If a second writer or an unattended run ever joins, restore
from there rather than rebuilding.

**(c) Who generates, who reviews?** Generation: the agent reading the
PROMPT-COREs at work time. Review: never the author — reviews go to models on
the operator's Ollama Cloud endpoint (`deepseek-v4-pro`, `gpt-oss`, `qwen3.5`,
`kimi`, `minimax`, `nemotron`, `gemma4`, `glm`), none of which is the author's
family, through `review_harness` so the packet ceiling and ledger rules apply,
and every result through `review-response`.

## The table

| module | installed | why / why not | acceptance command | planted-violation proof |
|---|---|---|---|---|
| `checkers/consistency_packet.py` | **yes** → `scripts/` | DeepReason states the same claim in several hand-edited documents (CLAUDE.md restates the frozen-surface list that `INV-frozen-surfaces.md` owns; `AUDIT_BASELINES.md` restates gate and instrument numbers). `docs_verify` checks claim-against-CODE; **nothing checks claim-against-CLAIM across documents.** That is exactly FR-14, and this tranche produced a live instance: the `treadle doctor` baseline row's line counts went stale the moment `treadle.toml` gained a third stage | `python3 scripts/consistency_packet.py --verify` | **proven 2026-08-24**: appended a line to the packet -> `FAIL: ... is stale` exit 1; added a pattern matching nothing -> `FAIL: no pattern matched in CLAUDE.md` exit 1; both restored green |
| `claims.json` | **yes** → repo root | the packet's row set; a claim not named here is a claim nobody is watching | (input to the above) | n/a — data |
| `checkers/review_harness.py` | **yes** → `scripts/` | the operator's own words open this tranche: "it gives genuinely independent review with my API key". Rung T2 established the value and two limits this module closes — a packet ceiling (FR-15) and provenance-is-not-reproducibility (FR-16) | the `verify_ledger` one-liner above | **proven 2026-08-24**: flipped one character of row 0's `reply_sha256` in a ledger copy -> `OK refused: transcript ... reply does not match the ledger's reply_sha256`. NullTransport smoke first: `rows: 1`, transcript header carries `reproducibility: none` |
| `LEDGER_FORMAT.md` | **yes** → `zoo/reviews/` | the ledger's grammar, beside the ledger, per the standard glue pattern | (read-only reference) | n/a — grammar |
| `skills/assembly` | **yes** → `skills/` | "always, first" (MODULES.md). Supersedes the 0.4.1 copy | (read at work time) | n/a — skill |
| `skills/review-response` | **yes** → `skills/` | named by the review acceptance: every review received gets a written disposition, each finding refuted with evidence or accepted with an action | (read at work time) | n/a — skill |
| `skills/minimal-pair-review` | **yes** → `skills/` | the reviewer's PROMPT-CORE for the review role. Supersedes the 0.4.1 copy, which lacks 0.5's rule 6 (the FR-20 mode check) | (read at work time) | n/a — skill |
| `checkers/battery_digest.py` + `FORMAT.md` | **no** | DeepReason produces no example batteries. Nothing in either acceptance command names it. Minimal-install rule | — | — |
| `checkers/influence_probe.py` | **no — deliberately, and this is the one worth revisiting** | DeepReason already ships `tools/blast_radius.py` as its committed answer to "can X affect Y", and `INV-frozen-surfaces.md` names it as the gate. `blast_radius` is STATIC (AST reachability, with an honest UNKNOWN bucket); `influence_probe` is INSTRUMENTED (measured reads). They answer the same question by different routes, and installing a second authority without deciding which governs is how FR-14 drift starts. **A tranche that reconciles them — most usefully by running `influence_probe` against a claim `blast_radius` has already ruled on — is the right home for this** | — | — |
| `skills/decision-mapping`, `expressibility-probe`, `precedent-transport`, `denotation-tests`, `discharge-typing`, `example-battery`, `mapping-table`, `semantic-round-trip`, `term-pinning` | **no** | not named by either acceptance command. Minimal-install rule. All remain readable at `tools/treadle0.5/skills/` and can be installed the moment a task names one | — | — |

## The skill-vintage hazard, stated because it is invisible otherwise

`skills/` already held twelve skills installed from **0.4.1** under this
tranche's deviation D2 ("its skills/ tree as shipped"). This install adds
three from **0.5**, two of which overwrite a 0.4.1 file of the same name. The
remaining overlapping names stay at 0.4.1 vintage, and nothing in a SKILL.md
records its own version. `skills/VINTAGE.md` therefore records which file came
from which release, and is the thing to update when any skill is replaced.

## What is degraded, stated per SETUP step 6

Nothing yet: an external reviewer IS available (the operator's Ollama Cloud
key). If that key is absent in a later session, `semantic-round-trip` is the
protocol that degrades first — an author back-translating their own pin is
recorded `ROUNDTRIP_VOID`, never clean.

## What this table does NOT check

Whether the two installed checkers are the RIGHT instruments for DeepReason —
only that each has a deterministic acceptance command and a recorded
planted-violation proof. Whether they earn their place is a question for the
first tranche that relies on one, and for adversarial review, not for this
table.
