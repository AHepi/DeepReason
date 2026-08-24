# treadle 0.2.0 — fixes for the 13-defect field report

Every numbered defect from the report, its fix, and where it lives.
APPLY: give this whole zip + this file to the agent that installed 0.1.0.

## Defect -> fix map

1. max_tokens too small, no empty-reply detection ->
   engine detects empty replies, records finish_reason, logs
   EMPTY_REPLY to evidence, auto-doubles the budget (cap:
   [driver] max_tokens_cap, default 32000) instead of burning
   candidates; shipped budgets raised (16000-20000). Files:
   src/treadle/engine.py, src/treadle/client.py (returns
   (content, finish_reason)), repo-assets/treadle.toml.
2. Failure evidence not persisted -> every attempt (raw replies,
   acceptance output, cone rejections) streams to
   .treadle/evidence/<task>-<ts>.log; BLOCKED board notes carry the
   evidence path. File: engine.py (Evidence class).
3. No stale-claim recovery -> at startup the driver requeues tasks
   CLAIMED under its own worker name (one driver per board);
   disable per-run with `treadle run --no-recover` or
   [driver] recover_stale = false. File: engine.py, cli.py.
4. TREADLE_BASE_URL silently ignored -> precedence is now
   env > toml > default, and doctor prints the resolved URL AND its
   source. Files: engine.py (load_config), cli.py.
5. No push story -> [driver] push = auto|true|false; auto pushes when
   a remote exists; on push failure or push=false, reviews run with
   the new gate flag --local-ok and verdicts are graded
   REVIEWED_LOCAL_OBJECTS (visible, never silent). Files: engine.py,
   repo-assets/swarm_gate.py.
6. Gate KeyError on missing optional keys -> load_board applies
   TASK_DEFAULTS schema migration; hand-written/old entries can no
   longer crash any command. File: repo-assets/swarm_gate.py.
7. add accepts what ready rejects, no repair path -> new gate command:
   swarm_gate.py edit ID [--goal|--cone|--base|--accept|
   --out-of-scope|--depends-on] — allowed in DRAFT/READY/BLOCKED,
   drops the task to DRAFT so ready re-validates, logged like every
   transition. File: repo-assets/swarm_gate.py.
8. Digests with no algorithm/producer -> example-battery rule 6
   rewritten: digests come ONLY from scripts/battery_digest.py
   --write; models write the literal PENDING-DIGEST; a hand-written
   hash is a fabrication even if correct. File:
   repo-assets/skills/example-battery/SKILL.md.
9. No machine grammar -> new rule 7: the battery grammar lives in
   zoo/batteries/FORMAT.md (template shipped:
   repo-assets/FORMAT.md); if absent, BLOCKED — never invent
   structure. Same SKILL.md.
10-13. battery_digest.py defects -> hardened reference shipped at
   repo-assets/battery_digest.py: --verify fails loudly on
   missing/renamed registry or wrong column counts (10, 11);
   --write reports the count and EXITS 1 on zero rows (12);
   designed order is `--write && --verify`, killing the
   PENDING-DIGEST catch-22 (13). Covered by tests.

Model updates (owner-directed, verified where possible):
- deepseek-v4-pro pinned to the DATED tag deepseek-v4-pro:0813-cloud —
  the plain :cloud tag silently moved to the new 0813 checkpoint,
  which is exactly the drift your eval criteria prohibit.
- Generator stages set to qwen8.3:cloud per owner arm-eval (small 8.3 >
  full 8.7/8.6). TAG UNVERIFIED against the endpoint: `treadle doctor`
  now queries /models and warns on any configured tag it cannot find —
  if it warns, get the exact tag from `ollama search qwen` and edit
  treadle.toml, or revert to glm-5.2:cloud.

## Agent apply instructions (exact)

    unzip -o treadle-0.2.0.zip -d ~/tools/     # overwrites 0.1.0 in place
    cd ~/tools/treadle && . .venv/bin/activate && pip install -e ".[dev]"
    pytest -q                                   # must print: 13 passed
    cd /path/to/target-repo
    cp ~/tools/treadle/repo-assets/swarm_gate.py scripts/swarm_gate.py
    cp ~/tools/treadle/repo-assets/skills/example-battery/SKILL.md skills/example-battery/SKILL.md
    cp ~/tools/treadle/repo-assets/battery_digest.py scripts/battery_digest.py
    mkdir -p zoo/batteries && cp ~/tools/treadle/repo-assets/FORMAT.md zoo/batteries/FORMAT.md
    # treadle.toml: merge by hand — take the new [driver] keys
    # (push, recover_stale, max_tokens_cap), the raised max_tokens,
    # and the model tags; keep any local routing you added.
    git add scripts skills zoo treadle.toml
    git commit -m "build: treadle 0.2.0 fixes per field report (defects 1-13)"
    ~/tools/treadle/.venv/bin/treadle --repo . doctor    # base_url source + model tags
    # every line OK (or explained WARN) before the next run

Report back: doctor output verbatim, and the evidence directory path
after your first run.
