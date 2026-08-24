# The machine, in pieces (module manifest)

Every piece below is independently deployable; the scripts are stdlib-only
Python with zero imports from each other or from treadle. Install exactly
what the task needs -- the copy line under each module is its entire
installation.

## M1 -- gate (coordination state machine)
FILE: scripts/swarm_gate.py        NEEDS: git, python3. No models, no treadle.
    cp repo-assets/swarm_gate.py <repo>/scripts/ && python3 scripts/swarm_gate.py init
USE ALONE FOR: multi-agent or multi-session git work (claims, cones,
commit-before-review, hash-chained log); a single crash-prone agent
(stale-claim discipline pays for itself alone); human teams wanting an
auditable task board with refusal semantics.

## M2 -- driver (treadle engine)
PKG: pip install -e <this zip>     NEEDS: M1 in the target repo, treadle.toml,
an OpenAI-compatible endpoint. THE ONLY PIECE THAT NEEDS A MODEL.
USE FOR: unattended generate->accept->commit loops over a board; multi-arm
review; provenance-ledgered model calls. Without M2 the rest of the machine
is still a full manual/agent workflow -- M2 only adds "hit play".

## M3 -- checkers (deterministic acceptance tools)
Each is one file, one grammar, usable as an acceptance command, a CI step,
or a hand tool -- with or without M1/M2:
- battery_digest.py (+ FORMAT.md): example batteries and ANY curated
  instance-set-with-registry document (test corpora, dataset cards,
  minimal-pair suites). Acceptance: `--write && --verify`.
- derivation_check.py (+ DERIVATION_FORMAT.md): replay of stepwise
  reasoning against a rule profile that is DATA -- inference systems,
  policy-compliance chains ("this conclusion followed from these premises
  under policy P"), approval-workflow audits, argument reconstruction.
  Authoring rules.json for a new domain is a reviewed transcription task.
- siblings (separate packages, same pattern): shuttle (repo audit via
  profiles), jacquard (finite-structure generation: countermodels,
  exhaustion, vacuity witnesses).

## M4 -- skills library (prompt-cores)
FILES: skills/*/SKILL.md           NEEDS: any LLM harness at all.
The PROMPT-CORE blocks work in Claude Code, Kimi, or raw API calls with no
treadle anywhere: term-pinning, example-battery, minimal-pair-review,
semantic-round-trip, mapping-table, denotation-tests, refutation-first,
discharge-typing, model-zoo-discipline, deduction, plus the swarm worker/
reviewer/orchestrator protocols.

## Known-good assemblies
- M1 alone ................ coordinated manual/agent repo work
- M3 alone ................ machine-checked documents, no board, no models
- M1+M3 ................... gated human workflow with deterministic acceptance
- M4 alone ................ discipline injected into any chat harness
- M1+M2+one M3 ............ a production line for ONE artifact type
- everything .............. the full formal-programme machine
Minimal-install rule: a piece not named by the task's acceptance command
or skill does not get installed.
