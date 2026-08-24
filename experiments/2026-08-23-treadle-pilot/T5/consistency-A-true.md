<!-- job=consistency-A-true model=deepseek-v4-pro:0813 role=REVIEWER -->
<!-- params={"max_tokens": 24000, "model": "deepseek-v4-pro:0813", "temperature": 0.0} -->
<!-- reproducibility: none -- params are provenance, not a replay guarantee (FR-16) -->
<!-- prompt_sha256=sha256:f19a592f0cf0ea9a2978a24d369f6ee6b29eb3bf2a2a9069daaeebf8232468f2 -->
<!-- inputs: zoo/reviews/CONSISTENCY_PACKET.md -->

Frozen-surface list is stated inconsistently across documents.

**Subject: frozen-surface list**
- FROZEN-CLAUDE: “the seven paths are `capabilities/state.py`, `harness.py`, `invariants.py`, `verification/`, `run_manifest.py`, `qualification.py`, and `llm/firewall.py`'s `route_fingerprint`.”
- FROZEN-INV: “## The five frozen surfaces ### 1. `capabilities/state.py` … ### 2. `harness.py` …” and later “### 5. Anything altering qualification subject digests — `qualification.py`”; it also treats `llm/firewall.py`'s `route_fingerprint` as frozen but does not list `verification/` as a frozen surface.
- FROZEN-CLAUDE also gives a different five-item list: “## Frozen surfaces (never touch without explicit operator approval) - `src/deepreason/capabilities/state.py` digests and event application - `src/deepreason/harness.py` event application / well-formedness - Replay-validation record formats; manifest schemas - Anything altering qualification subject digests - The append-only record itself, WITHIN the current version…”
Verdict: DISAGREE.

**Subject: root sweep status**
- FROZEN-INV: “Measure the difference rather than assuming it — the 42-root sweep below is the instrument.”
- SWEEP-CLAUDE: “The root sweep is RETIRED as an instrument (operator ruling 2026-08-22: "it just wastes time").”
- SWEEP-BASELINE: “root_sweep — RETIRED as an instrument (operator ruling 2026-08-22, ledgered in CLAUDE.md §Build and test): no audit, gate, or grant runs it anymore”
Verdict: DISAGREE.

Other subjects (old-run compatibility, task authoring) agree.

BEGIN_VERDICT
overall: INCONSISTENT
disagreements: 2
worst: "FROZEN-CLAUDE: 'the seven paths are `capabilities/state.py`, `harness.py`, `invariants.py`, `verification/`, `run_manifest.py`, `qualification.py`, and `llm/firewall.py`'s `route_fingerprint`' vs FROZEN-INV: '## The five frozen surfaces'"
END_VERDICT