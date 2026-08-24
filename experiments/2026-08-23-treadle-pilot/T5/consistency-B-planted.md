<!-- job=consistency-B-planted model=deepseek-v4-pro:0813 role=REVIEWER -->
<!-- params={"max_tokens": 24000, "model": "deepseek-v4-pro:0813", "temperature": 0.0} -->
<!-- reproducibility: none -- params are provenance, not a replay guarantee (FR-16) -->
<!-- prompt_sha256=sha256:5a314baa12202e33569d69859a812d842c1b97f26a52fe4fd5babcef3b4c6996 -->
<!-- inputs: experiments/2026-08-23-treadle-pilot/T5/PLANTED_PACKET.md -->

The frozen-surface list is stated in more than one document and does not agree.

**Subject: frozen-surface list**
- FROZEN-CLAUDE: “the seven paths are `capabilities/state.py`, `harness.py`, `invariants.py`, `verification/`, `run_manifest.py`, `scheduler/scheduler.py`, and `llm/firewall.py`'s `route_fingerprint`.”
- FROZEN-INV: “## The five frozen surfaces ### 1. `capabilities/state.py` — digests and event application ... ### 2. `harness.py` — event application and well-formedness ...” and later “### 5. Anything altering qualification subject digests — `qualification.py`” and “Treat its output format as frozen. `check: grep -q "def route_fingerprint" src/deepreason/llm/firewall.py`”
- FROZEN-CLAUDE also states a different list: “## Frozen surfaces (never touch without explicit operator approval) - `src/deepreason/capabilities/state.py` digests and event application - `src/deepreason/harness.py` event application / well-formedness - Replay-validation record formats; manifest schemas - Anything altering qualification subject digests - The append-only record itself, WITHIN the current version...”

Verdict: DISAGREE. One document says seven paths including `verification/` and `scheduler/scheduler.py`; another says five frozen surfaces and includes `qualification.py`; the same FROZEN-CLAUDE document elsewhere lists record formats, manifest schemas, and the append-only record instead.

**Subject: status of the “old runs owe the future nothing” operator law**
- OLDRUNS-CLAUDE: “**Old runs owe the future nothing; new versions optimise for new functions** (2026-08-14, operator's words verbatim: "old runs do not need to be valid or returnable by the way. What's important is that new versions are optimise...”
- OLDRUNS-ERRATA: “CLAUDE.md's operator law "Old runs owe the future nothing; new versions optimise for new functions" quotes that exact sentence and marks it **SUPERSEDED**: "new versions owe old roots neither validity nor readability, and no tranche owes a replay-byte-uncha...”

Verdict: DISAGREE. One excerpt presents the phrase as current operator law; the other says that same operator law is marked SUPERSEDED.

BEGIN_VERDICT
overall: INCONSISTENT
disagreements: 2
worst: "the seven paths are `capabilities/state.py`, `harness.py`, `invariants.py`, `verification/`, `run_manifest.py`, `scheduler/scheduler.py`, and `llm/firewall.py`'s `route_fingerprint`" vs "## The five frozen surfaces"
END_VERDICT