# AGENT_INSTALL — instructions for the LLM agent performing this install

You are an agent with shell access installing **treadle** into a git
repository that already uses the swarm gate. Follow these steps exactly;
verify each before the next. Report the final doctor output verbatim.

## 1. Unpack and install (own venv)

    unzip treadle-0.1.0.zip -d ~/tools/
    cd ~/tools/treadle
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -e ".[dev]"
    pytest -q          # must print: 5 passed

## 2. Prepare the target repository

    cd /path/to/target-repo        # ask the owner which repo if unclear

If `scripts/swarm_gate.py` is missing, copy it from
`~/tools/treadle/repo-assets/swarm_gate.py` and run
`python3 scripts/swarm_gate.py init`.

    cp ~/tools/treadle/repo-assets/treadle.toml .
    mkdir -p skills && cp -r ~/tools/treadle/repo-assets/skills/. skills/
    git add treadle.toml skills scripts/swarm_gate.py .swarm
    git commit -m "build: install treadle driver config, stage skills, gate"
    git push

## 3. Credentials

    export OLLAMA_API_KEY=<owner-provided key>     # if using https://ollama.com/v1
    # or run a local `ollama` daemon signed into cloud; then no key is needed
    # and base_url stays http://localhost:11434/v1

Edit `[driver] base_url` in treadle.toml accordingly. Never commit the key.

## 4. Verify

    ~/tools/treadle/.venv/bin/treadle --repo . doctor

Every line must read OK (WARN on credentials is acceptable only for
localhost). If any line reads MISS, fix that item; do not proceed.

## 5. Seed one task and hit play (owner-approved example)

    python3 scripts/swarm_gate.py add BAT-SameObservableLabel \
      --goal "Build the Reed example battery for SameObservableLabel per the terms inventory risk corridor" \
      --cone "zoo/batteries/same_observable_label/*" \
      --base $(git rev-parse HEAD) \
      --accept "test -s zoo/batteries/same_observable_label/BATTERY.md" \
      --out-of-scope "no pins, no record edits, no manifest changes"
    python3 scripts/swarm_gate.py ready BAT-SameObservableLabel
    ~/tools/treadle/.venv/bin/treadle --repo . plan     # confirm it is queued
    ~/tools/treadle/.venv/bin/treadle --repo . run --once

Then run the repo's audit and report results to the owner:

    git log --oneline -3
    python3 scripts/swarm_gate.py board

## Rules for you, the installing agent

- Obey every REFUSED_* line from any tool; never work around a refusal.
- Do not edit any sealed record, manifest, or file outside the paths named
  above. Do not run `treadle run` beyond `--once` without owner approval.
- If a step fails, stop, report the exact command and output, and wait.
