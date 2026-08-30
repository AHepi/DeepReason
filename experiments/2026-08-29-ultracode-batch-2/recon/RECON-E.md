# RECON-E — LANE E — two small execution-safety parks (E1 = PARKED.md P4 differential containment tests; E2 = PARKED.md P6 documentation)

Read-only reconnaissance, batch 2, produced before any lane work. Every claim cites file:line.

## Summary

E1 (P4) must convert ten confession-shaped assertions — assertions on strings the sandbox reports about ITSELF — into differentials that observe an OS-level effect. The ten live in two files: tests/test_contained_simulation_runner.py (lines 114, 146, 147, 376, 377) and tests/test_simulation_runner_default.py (lines 241, 242, 243, 327, 328). The model to copy is already committed: experiments/2026-08-27-change-execution-safety/proof/network_namespace_differential.sh, which runs the real interpreter INSIDE and OUTSIDE the backend's own probed prefix and compares. Scope is tests/ and probe scripts only; the map document that makes the standard enforceable is docs/map/SUB-verification.md, whose third Trap (lines 185-190) already STATES this rule and carries NO `check:` line — adding one is the map half. E2 (P6) is two edits to CLAUDE.md: (a) record that `pip install -e .` does not declare `jsonschema` or `pytest-xdist` although the documented gate needs both, in the Environment section's resync block that sessions actually paste; (b) replace the stale "expect ~3100 passed, 0 failed" at CLAUDE.md:162 with a pointer to docs/AUDIT_BASELINES.md, whose living baseline is "0 failed" with no passed count. Containment IS available on this host (measured: `('/usr/bin/unshare','--map-root-user','--net','--')` for both probes), so every proposed differential will really run rather than skip.

## Facts

- **P4's verbatim brief is PARKED.md lines 202-241; its WHAT names the exact defect shape.**
  - experiments/2026-08-27-change-execution-safety/PARKED.md:202-209 — "## P4 — MEDIUM: containment tests pin self-reported strings" / "**What.** `tests/test_contained_simulation_runner.py:134-149` asserts `reported[\"network\"] is False` and `reported[\"filesystem\"] == \"ephemeral scratch workdir\"` — values the backend reports about itself. A backend whose containment silently regressed would keep reporting them. This is how G1–G3 survived a committed containment proof."

- **P4's brief names its authority, its model, its scope and its gate verbatim.**
  - experiments/2026-08-27-change-execution-safety/PARKED.md:213-240 — "Route through dr-change-orchestrator. One tranche, one goal: every containment property claimed by verification/contained.py and oracle_sandbox.py is pinned by a DIFFERENTIAL that can fail, never by a string the backend reports about itself." ... "AUTHORITY: docs/map/INV-evidence-channels.md's first Trap (\"The flag is the cheap half. Assert the values a dispatch or a controller would actually CONSUME\"), and the standard docs_verify --audit already applies to map checks — a check that cannot fail is refused." ... "MODEL TO FOLLOW: experiments/2026-08-27-change-execution-safety/proof/network_namespace_differential.sh — it runs the real interpreter inside and outside the backend's own probed prefix and shows the interface list and the connect result differ. That is what a differential looks like." ... "SCOPE: tests/ only, plus whatever docs/map check makes the standard enforceable. No src changes — if a differential goes RED, that is a finding for a defect tranche, not something to fix here." ... "GATE: pytest tests/ -q -n 4, 0 failed."

- **THE ORIGINAL ESCAPE was a running-generator frame walk using only public attribute names, which reached the worker module's own globals and therefore the real builtins.**
  - experiments/2026-08-27-change-execution-safety/SAFETY.md:160 — "        box.append(gg.gi_frame.f_back.f_back.f_globals)"; SAFETY.md:168-172 — "`gi_frame`, `f_back` and `f_globals` are all public attribute names. While the generator is running, its frame's `f_back` is `simulate`'s frame, and `f_back.f_back` is the worker's own `run()` frame, whose `f_globals` is the worker module namespace — which holds the real `builtins`, `sys`, `json`, `random` and `math` modules."

- **The escape produced three demonstrated effects, each while the recorded verdict stayed `pass`: a file written outside the scratch dir, an arbitrary shell command at harness privilege, and an outbound TCP connection to the open internet from the code-testing channel.**
  - SAFETY.md:286-292 — "E1 BROKEN (d): file access is NOT confined to the sandbox directory / verdict=pass ... file written OUTSIDE the ephemeral scratch dir: True / contents: 'ESCAPED'"; SAFETY.md:316-318 — "E2 BROKEN (e): arbitrary shell commands run at harness privilege / verdict=pass  os.system('true') returncode in output:"; SAFETY.md:368-371 — "E3 BROKEN: the SAME escape on the code-testing channel, which is ON / exec-oracle verdict on the hostile candidate: pass / marker written: True / network result from inside the sandbox: 'NETWORK_REACHED'"

- **THE REASON IT SURVIVED A COMMITTED PROOF is stated twice in SAFETY.md: the committed suite asserted the backend's own strings, so no committed test covered either broken property.**
  - SAFETY.md:295-298 — "**No committed test covers this.** `tests/test_contained_simulation_runner.py:134` asserts `reported[\"filesystem\"] == \"ephemeral scratch workdir\"` — a string the backend reports about itself, which is exactly the shape `DR-INV-evidence-channels`'s first Trap warns about."; SAFETY.md:196-199 — "The committed suite asserts `reported[\"network\"] is False`, which is the backend describing itself; this is a differential."

- **G5 is the gap row that records this, and it is rated Medium precisely because it is why G1-G3 went unnoticed.**
  - SAFETY.md:399 — "| G5 | Containment properties are pinned by self-reported strings (`\"network\": False`, `\"filesystem\": \"ephemeral scratch workdir\"`) rather than by differentials that could fail. | `tests/test_contained_simulation_runner.py:134-149` | **Medium — this is why G1–G3 went unnoticed** |"

- **CONFESSION #1 and #2: test_contained_simulation_runner.py pins the contained backend's self-reported network flag and filesystem string.**
  - tests/test_contained_simulation_runner.py:145-147 — "    reported = _backend().resource_limits()" / "    assert reported[\"network\"] is False" / "    assert reported[\"filesystem\"] == \"ephemeral scratch workdir\""

- **CONFESSION #3: the same file pins the self-reported network-denial mechanism label on the fingerprint.**
  - tests/test_contained_simulation_runner.py:114 — "    assert fingerprint[\"network_denial\"] == \"namespace_unshared\""

- **CONFESSION #4 and #5: the same file re-pins both strings a second time, on the receipt written by a real end-to-end controller run.**
  - tests/test_contained_simulation_runner.py:376-377 — "    assert receipt.resource_limits[\"network\"] is False" / "    assert receipt.resource_limits[\"filesystem\"] == \"ephemeral scratch workdir\""

- **CONFESSIONS #6, #7, #8: test_simulation_runner_default.py pins the same three strings, under a comment that explicitly claims they prove execution happened under containment.**
  - tests/test_simulation_runner_default.py:238-243 — "    # Executed UNDER the R2 containment, asserted on the receipt rather than" / "    # assumed from the profile name." / "    limits = backend.resource_limits()" / "    assert limits[\"network\"] is False" / "    assert limits[\"network_denial\"] == \"namespace_unshared\"" / "    assert result.fingerprint[\"network_denial\"] == \"namespace_unshared\""

- **CONFESSIONS #9 and #10: the same file re-pins two of them on the default-policy end-to-end receipt.**
  - tests/test_simulation_runner_default.py:327-328 — "    assert attempt.fingerprint[\"network_denial\"] == \"namespace_unshared\"" / "    assert receipt.resource_limits[\"network\"] is False"

- **Every one of those strings is a hardcoded literal in a dict the backend returns: `resource_limits()` never consults the probe, so it cannot go false when containment regresses.**
  - src/deepreason/verification/contained.py:505-522 — "    def resource_limits(self) -> dict[str, Any]:" ... "            \"filesystem\": \"ephemeral scratch workdir\"," (line 519) / "            \"network\": False," (line 520) / "            \"network_denial\": \"namespace_unshared\"," (line 521)

- **Likewise the fingerprint's network_denial label is a literal, independent of whether the prefix is applied.**
  - src/deepreason/verification/contained.py:493-503 — "    def fingerprint(self) -> dict[str, Any]:" ... "            \"network_denial\": \"namespace_unshared\"," (line 502)

- **The prefix that the literals describe is applied only at the Popen call, and nothing observable ties the literal to it.**
  - src/deepreason/verification/contained.py:641-650 — "                process = subprocess.Popen(  # noqa: S603 - frozen containment command" / "                    [*prefix, sys.executable, \"worker.py\"]," / "                    cwd=scratch," ... "                    preexec_fn=lambda: _apply_containment_limits(limits),"

- **The rlimit numbers reported are pinned only against another self-report (`_containment_limits`), never against what the child process actually gets. NOFILE, NPROC and FSIZE have no effect-observing test anywhere.**
  - tests/test_contained_simulation_runner.py:148-149 — "    for key in (\"cpu_seconds\", \"memory_bytes\", \"fsize_bytes\", \"nofile\", \"nproc\"):" / "        assert reported[key] == limits[key]"; the applying function is src/deepreason/verification/contained.py:412-416 — "    resource.setrlimit(\n        resource.RLIMIT_FSIZE, (limits[\"fsize_bytes\"], limits[\"fsize_bytes\"])\n    )" / "    resource.setrlimit(resource.RLIMIT_NOFILE, (limits[\"nofile\"], limits[\"nofile\"]))" / "    resource.setrlimit(resource.RLIMIT_NPROC, (limits[\"nproc\"], limits[\"nproc\"]))"

- **The contained worker's environment is pinned only as the dict the pure function returns — a confession about what the child WILL get, never read back from a child.**
  - tests/test_contained_simulation_runner.py:117-131 — "def test_worker_environment_is_a_fixed_allowlist(monkeypatch):" ... "    environment = _contained_environment(\"/scratch/example\")" / "    assert set(environment) == {" ... "    assert not any(\"DEEPREASON\" in key or \"KEY\" in key for key in environment)"

- **The code-testing channel's worker environment scrub has NO test anywhere in tests/.**
  - src/deepreason/oracle_sandbox.py:44-45 defines it — "def _worker_environment() -> dict[str, str]:" / "    \"\"\"Minimal environment plus the exact package root running in the parent.\"\"\""; `grep -rn "_worker_environment" tests/` returns no .py match (only two __pycache__ binaries and no source line).

- **TWO GENUINE DIFFERENTIALS ALREADY EXIST and are the shape to copy — one pins the actual argv of a real launch, one runs the real probe inside the prefix. Both live in tests/test_sandbox_guard.py's OS-layer section.**
  - tests/test_sandbox_guard.py:479-486 — "def test_the_code_testing_worker_runs_behind_the_network_namespace(monkeypatch):" / "    \"\"\"Wiring: the probed prefix really is the head of the worker command.\n\n    Asserted on the ACTUAL argv of a real `run_isolated` call, not on a\n    configuration value the module reports about itself — the failure shape\n    SAFETY.md G5 records, where a self-reported `\"network\": False` outlived the\n    containment it described.\n    \"\"\""; and tests/test_sandbox_guard.py:520-527 — "def test_the_network_namespace_actually_denies_network():" / "    \"\"\"The differential the committed suite never carried."

- **That second differential is ONE-ARMED: it asserts only the inside arm, so on a host whose only interface is `lo` it would pass without measuring anything. The committed shell model runs BOTH arms.**
  - tests/test_sandbox_guard.py:553-554 — "    assert inside[\"reached\"] is False" / "    assert inside[\"interfaces\"] == [\"lo\"], inside[\"interfaces\"]" (no outside arm anywhere in the function); contrast experiments/2026-08-27-change-execution-safety/proof/network_namespace_differential.sh:13-16 — "echo \"=== INSIDE the backend's own probed prefix (unshare --map-root-user --net) ===\"" / "/usr/bin/unshare --map-root-user --net -- python3 \"$PROBE\"" / "echo \"=== OUTSIDE (host namespace) ===\"" / "python3 \"$PROBE\""

- **The existing shell differential's recorded output is the reference for what a passing two-armed differential looks like.**
  - experiments/2026-08-27-change-execution-safety/proof/network_namespace_differential.out:1-6 — "=== INSIDE the backend's own probed prefix (unshare --map-root-user --net) ===" / "CONNECT_DENIED OSError [Errno 101] Network is unreachable" / "INTERFACES [(1, 'lo')]" / "=== OUTSIDE (host namespace) ===" / "CONNECT_OK" / "INTERFACES [(1, 'lo'), (2, 'ifb0'), (3, 'ifb1'), (4, 'eth0')]"

- **The existing differentials cover the CODE-TESTING channel's prefix, not the CONTAINED backend's. The two backends run SEPARATE, duplicated probes: contained.py has its own copy and never imports sandbox_os.**
  - src/deepreason/verification/contained.py:457-487 defines its own — "    def containment_prefix(cls) -> tuple[str, ...]:" ... "        unshare = shutil.which(\"unshare\")" (line 469) / "            for flags in ((\"--map-root-user\", \"--net\"), (\"--net\",)):" (line 471); and contained.py's import block (lines 41-43) reads "from deepreason.canonical import canonical_json, sha256_hex" / "from deepreason.sandbox_guard import WORKER_GUARD_SOURCE" / "from deepreason.verification.simulation import (" — no sandbox_os import.

- **sandbox_os.py's own docstring CLAIMS contained.py uses it, which the import list above falsifies. This is a live docs-vs-code contradiction adjacent to the lane.**
  - src/deepreason/sandbox_os.py:16-19 — "So the probe lives here, once, and both backends that execute untrusted Python\nuse it: ``verification/contained.py`` (``sandboxed_python_v1``, opt-in) and\n``oracle_sandbox.py`` (the code-testing channel, on by default and — until this\nmodule — carrying no OS boundary whatsoever)."

- **Containment is AVAILABLE on this host and both probes resolve to the same prefix, so proposed differentials will really execute rather than skip.**
  - measured this session: `python -c "from deepreason.verification.contained import ContainedSimulationBackend; from deepreason.sandbox_os import network_denial_prefix; print(ContainedSimulationBackend.containment_prefix()); print(network_denial_prefix())"` → "contained prefix: ('/usr/bin/unshare', '--map-root-user', '--net', '--')" / "sandbox_os prefix: ('/usr/bin/unshare', '--map-root-user', '--net', '--')"

- **The `"filesystem": "ephemeral scratch workdir"` string names a jail that does not exist: the prefix carries --net only, no --mount. A differential on it would go RED against the claim.**
  - SAFETY.md:397 (gap G2) — "| G2 | No mount namespace or filesystem jail: `cwd` is the only confinement, and `resource_limits()` reports `\"filesystem\": \"ephemeral scratch workdir\"` as though it were one. | `contained.py:463`, `:508-515`, `:624-642` | **High** |"; and PARKED.md:487-491 (P9) — "Consider the cheaper honest alternative first: keep cwd + RLIMIT_FSIZE and STOP reporting \"filesystem\": \"ephemeral scratch workdir\" from resource_limits(), which claims a confinement that does not exist. A truthful weaker string beats a false stronger one."

- **The scratch directory's real, observable behaviour (created, used as cwd, destroyed) IS already pinned by effect and can carry the honest half of the filesystem claim.**
  - tests/test_contained_simulation_runner.py:213-215 — "    # The scratch working directory is disposable: nothing survives the run." / "    assert \"scratch\" in captured" / "    assert not Path(captured[\"scratch\"]).exists()"; the launch kwarg is src/deepreason/verification/contained.py:643 — "                    cwd=scratch,"

- **MAP HALF: docs/map/SUB-verification.md already STATES the P4 rule as a Trap, and that Trap carries NO `check:` line — the only Trap in its neighbourhood without one.**
  - docs/map/SUB-verification.md:185-191 — "- **A containment property pinned by a string the backend reports about itself\n  is not pinned.** `resource_limits()` returned `\"network\": False` and\n  `\"filesystem\": \"ephemeral scratch workdir\"` throughout the period when\n  neither was true of model-authored code. The committed suite asserted those\n  strings. Assert a DIFFERENTIAL — run the probe inside and outside the\n  containment and compare — or the test cannot fail for the reason it exists." followed by a blank line at :191 and the next bullet at :192 — no `check:` between them. The two Traps immediately above DO carry checks: :176 "`check: python -m pytest tests/test_sandbox_guard.py -q -k \"contained or declarative or brokered or frozen_worker\"`" and :184 "`check: python -m pytest tests/test_sandbox_guard.py -q -k \"network\"`".

- **The authority P4 cites for the standard is INV-evidence-channels.md's first Trap, which is present verbatim.**
  - docs/map/INV-evidence-channels.md:173-178 — "- **A default that is `True` over a road that is severed.** The flag is the\n  cheap half. Assert the values a dispatch or a controller would actually\n  CONSUME — a non-empty allowlist, a positive request budget, a controller that\n  constructs against the compiled manifest — or the registry states an\n  enablement the run cannot use."

- **verify_root itself CONSUMES the receipt's `resource_limits["network"]` field, so the field cannot simply be deleted from assertions without weakening a replay check.**
  - src/deepreason/invariants.py:1854 — "                    or receipt.resource_limits.get(\"network\") is not False"

- **E1's frozen-surface boundary: `verification/` is frozen surface 3, so any src fix to the false filesystem string, or to deduplicate the probe, is a STOP for this lane.**
  - docs/map/INV-frozen-surfaces.md:47-51 — "### 3. Replay-validation record formats — `invariants.py`, `verification/`" / "`verify_root` and the epistemic-check report. Their output shape is compared across runs and across time; a format change silently reinterprets every stored verdict."; and the same document's list header at :29 — "## The five frozen surfaces"

- **P6's verbatim brief is PARKED.md lines 278-328; its WHAT names both dependencies and both files.**
  - experiments/2026-08-27-change-execution-safety/PARKED.md:278-288 — "## P6 — LOW: the documented gate needs two dependencies the install does not declare" / "**What.** CLAUDE.md's gate command is `pytest tests/ -q -n 4`, and `tests/test_schema_carries_every_prose_rule.py:170` imports `jsonschema`. Neither `pytest-xdist` (which `-n 4` requires) nor `jsonschema` appears in `pyproject.toml` — `dependencies` has three entries and `optional-dependencies.dev` has `pytest` and `ruff` only. A fresh container that runs the documented setup and then the documented gate gets one failure that looks like a code defect and is not. This tranche hit it: `1 failed, 4334 passed` on `ModuleNotFoundError: No module named 'jsonschema'`."

- **P6's brief additionally instructs a census from the tests, and names the CLAUDE.md baseline correction as a same-commit obligation.**
  - PARKED.md:311-322 — "THE FIX: declare what the gate actually needs in optional-dependencies.dev — at minimum jsonschema and pytest-xdist. Take the census from the tests rather than from this prompt: grep the suite for third-party imports and reconcile the whole set against pyproject.toml, so this is fixed once rather than one module at a time." / "WHILE YOU ARE THERE: CLAUDE.md's Build-and-test section says \"expect ~3100 passed, 0 failed\". The 2026-08-27 run collected 4334 passed, 15 skipped. Update the baseline in the same commit and record the new number, so the next session can tell a real regression from a stale expectation. Check docs/AUDIT_BASELINES.md for the same number."

- **VERIFIED: pyproject.toml's runtime dependencies are exactly three — pydantic, pyyaml, fastembed. Neither jsonschema nor pytest-xdist appears.**
  - pyproject.toml:11-21 — "dependencies = [" / "    \"pydantic>=2.7\"," / "    \"pyyaml>=6.0\"," ... "    \"fastembed>=0.3\"," / "]"

- **VERIFIED: the dev extra carries exactly pytest and ruff. No pytest-xdist, no jsonschema.**
  - pyproject.toml:23-27 — "[project.optional-dependencies]" / "dev = [" / "    \"pytest>=8.0\"," / "    \"ruff>=0.4\"," / "]"

- **There is no setup.py or setup.cfg — pyproject.toml is the sole dependency declaration.**
  - `ls /home/user/DeepReason/setup.py /home/user/DeepReason/setup.cfg` → "ls: cannot access '/home/user/DeepReason/setup.py': No such file or directory" / "ls: cannot access '/home/user/DeepReason/setup.cfg': No such file or directory"

- **The third-party import census over tests/ and mini/ yields exactly four non-stdlib, non-first-party top-level modules: pydantic (declared), pytest (declared dev), yaml (declared as pyyaml), and jsonschema (NOT declared). No other undeclared import exists.**
  - AST census run this session over tests/**/*.py and mini/**/*.py: "jsonschema 1 tests/test_schema_carries_every_prose_rule.py:170" / "pydantic 55 ..." / "pytest 311 ..." / "yaml 7 tests/test_config.py:6" (remaining hits — e31_benchmark, informal_ab, live_run, scripts — are in-repo modules).

- **jsonschema is imported at exactly ONE site in the whole repo, and it is a test.**
  - `grep -rn "import jsonschema" tests src tools scripts mini` → sole hit "/home/user/DeepReason/tests/test_schema_carries_every_prose_rule.py:170:    import jsonschema"

- **CRUCIAL AND UNRECORDED IN P6: that file ALREADY has a `pytest.importorskip` guard twelve lines later, which the bare import on line 170 defeats. Deleting line 170 alone makes the gate green on a container without jsonschema.**
  - tests/test_schema_carries_every_prose_rule.py:170-182 — "    import jsonschema" (line 170) / "    import pytest" (171) ... "    jsonschema = pytest.importorskip(\"jsonschema\", reason=\"optional checker\")" (line 182)

- **pytest-xdist is not an import at all — it is required only by the `-n 4` flag in the documented gate command.**
  - CLAUDE.md:161 — "    pytest tests/ -q -n 4                       # full gate, ~8 min"; the census above found no `xdist` import in tests/.

- **CLAUDE.md's Environment resync block — the thing a session actually pastes after a rollback — installs only the package and says nothing about the gate's own dependencies.**
  - CLAUDE.md:130-133 — "    git log --oneline -1        # stale head? resync:" / "    git fetch origin <branch> && git checkout -B <branch> origin/<branch>" / "    which deepreason || pip install -e . --break-system-packages -q" / "    ls experiments/live_research_*/env   # gitignored credential file"

- **CLAUDE.md's Build-and-test block carries the stale count and a stale duration.**
  - CLAUDE.md:159-162 — "    pip install -e . --break-system-packages    # editable install; the" / "                                                # CLI and live runs share it" / "    pytest tests/ -q -n 4                       # full gate, ~8 min" / "                                                # expect ~3100 passed, 0 failed"

- **"~3100" is the ONLY occurrence of a passed-count expectation in CLAUDE.md; the other numeric mention is a commit-message convention with a placeholder N.**
  - `grep -n "3100\|passed," CLAUDE.md` → only "CLAUDE.md:162:                                                # expect ~3100 passed, 0 failed" and "CLAUDE.md:306:  why, the live evidence (run ids), and \"Full gate: N passed, 0\""

- **docs/AUDIT_BASELINES.md's full-gate baseline is stated as 0 FAILED, with NO passed count, plus a named flaky set under -n 4.**
  - docs/AUDIT_BASELINES.md:14-24 — "- **Full pytest gate** (`python -m pytest tests/ -q -n 4`):\n  **0 failed.**" ... "  Known-flaky under `-n 4`, green in serial re-run: 3 tests in\n  `tests/test_mcp_run.py`, 2 in `tests/test_mcp_scratch_bridge.py`\n  (thread-join timing)."

- **docs/AUDIT_BASELINES.md ALREADY carries the exact remedy command for the install gap — including pytest-xdist and jsonschema by name — and CLAUDE.md never points there.**
  - docs/AUDIT_BASELINES.md:49-56 — "  ENVIRONMENT, or the number is meaningless: this container resolves\n  `python` to `/usr/local/bin/python` while `pip` resolves to\n  `/usr/bin/pip`, so `pip install -e .` arms a DIFFERENT interpreter\n  than the checks invoke and every `python -m pytest` check dies with\n  `No module named pytest`. Measured cost of getting this wrong: 502\n  failures, none of them real. Run `python -m pip install -e . pytest\n  pytest-xdist jsonschema --break-system-packages` and confirm\n  `python -m pytest --version` before trusting any docs_verify total."

- **docs/AUDIT_BASELINES.md declares itself the living source and states its own move protocol, which permits a same-commit update in a non-audit tranche.**
  - docs/AUDIT_BASELINES.md:3-8 — "Read by the dr-audit family (PRECEDENCE 2): a delta from these values\nis a finding; a match is disposition `baseline`. This file moves only\nin a non-audit tranche, in the same commit as whatever moved the\nvalue, with the audit family's close gate re-run there. A baseline\nbelieved wrong during an audit is rowed and parked, never edited\nmid-audit."

- **The empirically observed failure P6 describes is recorded verbatim in DELIVERY.md, with the correct diagnosis that it is an environment gap and a note that CLAUDE.md is where it should be recorded.**
  - experiments/2026-08-27-change-execution-safety/DELIVERY.md:127-152 — "$ python -m pytest tests/ -q -n 4" / "1 failed, 4334 passed, 15 skipped in 994.44s (0:16:34)" / "FAILED tests/test_schema_carries_every_prose_rule.py::test_alias_bearing_fields_name_their_legal_values_in_the_schema" / "E       ModuleNotFoundError: No module named 'jsonschema'" ... "Recorded rather than smoothed over, because the container-rollback note in CLAUDE.md's Environment section does not mention `jsonschema` and the next fresh session will hit the same wall." / "Note for the baseline: CLAUDE.md's \"expect ~3100 passed\" is stale — this run collected 4334 passed, 15 skipped."

- **The count has already moved again since P6 was written: the same tranche's closing gate reported 4374 passed.**
  - experiments/2026-08-27-change-execution-safety/DELIVERY.md:362-363 — "$ python -m pytest tests/ -q -n 4" / "4374 passed, 6 skipped in 823.17s (0:13:43)"

- **CURRENT collected total measured this session is 4491 — so any hardcoded number in CLAUDE.md is stale on arrival, which is the argument for pointing at AUDIT_BASELINES.md rather than writing a new literal.**
  - `python -m pytest tests/ -q --collect-only` this session → "4491 tests collected in 8.66s"

- **CLAUDE.md's "~8 min" duration is also stale: three recorded full-gate runs took 13:43, 14:35 and 16:34.**
  - DELIVERY.md:363 — "4374 passed, 6 skipped in 823.17s (0:13:43)"; DELIVERY.md:129 — "1 failed, 4334 passed, 15 skipped in 994.44s (0:16:34)"; SAFETY.md:44 — "4364 passed, 6 skipped in 875.84s (0:14:35)"

- **jsonschema and pytest-xdist are BOTH currently installed in this container, so E1's and E2's gate runs will not themselves reproduce the gap — the claim must be argued from pyproject, not from an import error here.**
  - measured this session: `python -c "import jsonschema..."` → "jsonschema 4.26.0"; `python -c "import xdist..."` → "xdist 3.8.0"

- **The lane's map ids, per the map preflight rule: the routing table names the two INV documents and the seam this work sits on.**
  - docs/map/INDEX.md:23-25 — "| know whether you are allowed to change it | `INV-frozen-surfaces.md` — **first, always** |" / "| know which outside-reaching channels a run has, and how one is turned off | `INV-evidence-channels.md` |" / "| know whether a channel that says ON can actually reach the capability it enables | `SEAM-capabilities-x-channels.md` |"; and INDEX.md:56 — "| `SUB-verification.md` | `verify_root`, replay validation, epistemic checks. **Frozen** |"

- **SUB-verification.md owns the containment surface and already routes its containment-shape checks at tests/test_contained_simulation_runner.py.**
  - docs/map/SUB-verification.md:149 — "| Sandbox resource limits or the containment shape | `_CPU_SECONDS` / `_MEMORY_LIMIT` / `_IPC_LIMIT` in `simulation.py`; `_containment_limits` and `containment_prefix` in `contained.py`; `_sandbox.py` for seccomp | `python -m pytest tests/test_contained_simulation_runner.py -q` |"

- **ADJACENT, OUT OF P4's NAMED SCOPE: two more self-report pins exist outside contained.py/oracle_sandbox.py. One is already differential-backed; the other is not.**
  - tests/test_workload_formal.py:152-153 — "    assert result.verdict == \"pass\"" / "    assert result.detail[\"network_isolated\"] is True" (differential-backed: the program at :133-141 calls `socket.socket()` and `raise SystemExit(2)` if it succeeds); versus tests/test_lean_backend.py:84 — "    assert result.fingerprint[\"network\"] is False", whose source is an unconditional literal at src/deepreason/verification/lean.py:125 — "            \"network\": False,"

- **The declarative in-process simulation backend reports its own filesystem confinement too, with a different string and no OS mechanism.**
  - src/deepreason/verification/simulation.py:490-497 — "        return {" ... "            \"filesystem\": \"no candidate file builtins\"," (line 495) / "            \"network\": False," (line 496)

- **Effect-observing tests DO already exist for cpu and memory containment on both channels — those properties do not need new differentials.**
  - tests/test_contained_simulation_runner.py:231-232 — "    assert result.verdict == \"fail\"" / "    assert result.trace[\"error\"] == \"deterministic step limit exceeded\""; tests/test_contained_simulation_runner.py:246-247 — "    assert result.verdict == \"overrun\"" / "    assert result.trace[\"sandbox_abort\"] == \"resource containment\""; tests/test_oracle.py:864-865 — "    assert verdict == OVERRUN" / "    assert trace[\"sandbox_abort\"]"

- **The probe scripts available to this lane are five files in one directory, three of them executable evidence and two of them recorded outputs.**
  - `ls experiments/2026-08-27-change-execution-safety/proof/` → "containment_probe.py", "containment_probe_AFTER.out", "containment_probe_BEFORE.out", "mutation_proof.out", "mutation_proof.sh", "network_namespace_differential.out", "network_namespace_differential.sh"

- **containment_probe.py is self-cleaning and re-runnable, which is why it can be lifted into tests without leaving artifacts.**
  - experiments/2026-08-27-change-execution-safety/proof/containment_probe.py:203-210 — "    section(\"cleanup\")" / "    for path in (marker, net_marker):" / "        path.unlink(missing_ok=True)" ... "    print(\"  markers removed:\", not MARKER_DIR.exists())"

- **The escape's end-to-end form is already committed as a test constant, so new differentials can reuse it rather than re-deriving the exploit.**
  - tests/test_sandbox_guard.py:60-69 — "FRAME_WALK = (\n    \"    box = []\\n\"\n    \"    def g():\\n\"\n    \"        box.append(gg.gi_frame.f_back.f_back.f_globals)\\n\"\n    \"        yield 1\\n\"\n    \"    gg = g()\\n\"\n    \"    for v in gg:\\n\"\n    \"        break\\n\"\n    \"    w = box[0]\\n\"\n)"


## Files

- `/home/user/DeepReason/experiments/2026-08-27-change-execution-safety/PARKED.md` (read) — Source of both briefs. P4 at lines 202-241, P6 at lines 278-328. Read in full this session; the lane should cite line numbers, not re-read.
- `/home/user/DeepReason/experiments/2026-08-27-change-execution-safety/SAFETY.md` (read) — The evidence P4 rests on: the escape at :160-172, E1/E2/E3 at :286-292/:316-318/:368-371, the G5 gap row at :399, and the two 'no committed test covers this' statements at :196-199 and :295-298.
- `/home/user/DeepReason/experiments/2026-08-27-change-execution-safety/DELIVERY.md` (read) — E2's empirical citation: the jsonschema gate failure at :127-152 and the closing 4374 count at :362-363. Cite, do not re-derive.
- `/home/user/DeepReason/experiments/2026-08-27-change-execution-safety/proof/network_namespace_differential.sh` (read) — The MODEL P4 names for what a differential looks like. Two arms, inside and outside. Copy its shape into pytest form.
- `/home/user/DeepReason/experiments/2026-08-27-change-execution-safety/proof/network_namespace_differential.out` (read) — The recorded reference output a passing two-armed differential must reproduce.
- `/home/user/DeepReason/experiments/2026-08-27-change-execution-safety/proof/containment_probe.py` (read) — The hostile-program driver and its self-cleaning marker discipline; the source of the reusable escape text and the _run_contained helper shape.
- `/home/user/DeepReason/tests/test_contained_simulation_runner.py` (read-write) — E1's primary target. Five confessions at lines 114, 146, 147, 376, 377; the self-to-self rlimit comparison at 148-149; the pure-function environment confession at 117-131; and the already-effect-based scratch assertion at 213-215 to build on.
- `/home/user/DeepReason/tests/test_simulation_runner_default.py` (read-write) — E1's second target. Five confessions at lines 241, 242, 243, 327, 328 — including a comment at 238-239 claiming they prove execution under containment, which they do not.
- `/home/user/DeepReason/tests/test_sandbox_guard.py` (read-write) — Owns the '--- the OS layer, which does not depend on the guard being right ---' section at :476. Holds the two genuine differentials to copy (:479-517 argv recorder, :520-554 prefix probe), the reusable FRAME_WALK constant at :60-69, and the one-armed differential at :553-554 that needs its outside arm. Best home for the new contained-backend differentials.
- `/home/user/DeepReason/src/deepreason/verification/contained.py` (read) — READ ONLY — frozen surface 3. The literals under test: fingerprint at :493-503, resource_limits at :505-522 (filesystem :519, network :520, network_denial :521), the applying limits at :394-416, the duplicated probe at :457-487, and the Popen launch at :641-650 that a recorder must observe.
- `/home/user/DeepReason/src/deepreason/oracle_sandbox.py` (read) — READ ONLY for this lane. The code-testing channel's launch at :112-126 (prefix applied), fail-closed rlimits at :154-194, and the completely untested environment scrub at :44-68.
- `/home/user/DeepReason/src/deepreason/sandbox_os.py` (read) — The shared probe. Its docstring at :16-19 claims contained.py uses it; contained.py's imports at :41-43 falsify that. network_denial_prefix at :54-83 and reset_probe_cache at :90-94 (useful for tests that simulate an unequipped host).
- `/home/user/DeepReason/src/deepreason/invariants.py` (read) — READ ONLY — frozen surface 3. Line 1854 consumes receipt.resource_limits['network'], which is why that field cannot simply be dropped from assertions without weakening a replay check.
- `/home/user/DeepReason/docs/map/SUB-verification.md` (read-write) — E1's map half. The Trap at :185-190 already states P4's rule and carries NO check: line — adding one that runs the new differentials is the minimum map move. Verified-at and the Traps neighbourhood at :157-191 give the surrounding pattern.
- `/home/user/DeepReason/docs/map/INV-evidence-channels.md` (read) — The AUTHORITY P4 cites: the first Trap at :173-178 ('the flag is the cheap half'). Its 2026-08-27 Trap at :208-229 already carries the check at :229 that runs the existing sandbox_guard differentials.
- `/home/user/DeepReason/docs/map/INV-frozen-surfaces.md` (read) — Read BEFORE designing, per the map rule. Surface 3 at :47-53 covers verification/ and invariants.py; the five-surface header is at :29. Confirms tests/, docs/ and pyproject.toml are unfrozen.
- `/home/user/DeepReason/CLAUDE.md` (read-write) — E2's only mandatory write. Environment resync block at :130-133 (edit a), Environment prose at :135-155, Build-and-test block at :159-162 (edit b, the stale '~3100 passed' and '~8 min').
- `/home/user/DeepReason/docs/AUDIT_BASELINES.md` (read) — E2's living-source target. Full-gate baseline at :14-24 ('0 failed', no passed count, named flaky set); the install remedy already spelled out at :49-56; the file's own move protocol at :3-8. Becomes read-write ONLY if the lane records a freshly measured passed count there.
- `/home/user/DeepReason/pyproject.toml` (read) — E2's verification: dependencies at :11-21 (pydantic, pyyaml, fastembed) and optional-dependencies.dev at :23-27 (pytest, ruff). Confirms neither jsonschema nor pytest-xdist is declared. WRITE ONLY IF the parent widens E2's scope beyond docs — see stops.
- `/home/user/DeepReason/tests/test_schema_carries_every_prose_rule.py` (read) — The single jsonschema import site, line 170, twelve lines above a pytest.importorskip at 182 that the bare import defeats. Read to confirm the one-line alternative fix; becomes read-write only if the parent authorizes the test fix in addition to the doc edit.
- `/home/user/DeepReason/tests/test_workload_formal.py` (read) — Adjacent self-report at :153, already backed by a real socket differential at :133-152 — the positive example of a confession that is safe because an effect stands behind it.
- `/home/user/DeepReason/tests/test_lean_backend.py` (read) — Adjacent unbacked self-report at :84 against a hardcoded literal in lean.py:125, under a FAKE lean fixture. Outside P4's named scope (contained.py + oracle_sandbox.py); report, do not fix.
- `/home/user/DeepReason/tests/test_oracle.py` (read) — Line 847-871 is the code-testing channel's real memory-bomb differential; proves the memory property by effect and needs no work.

## Work items

### E1-0 — MAP PREFLIGHT. Record the ids in the tranche's first artifact: DR-SUB-verification (owns verification/, FROZEN), DR-INV-evidence-channels (the authority Trap), DR-INV-frozen-surfaces (surface 3 boundary), DR-SEAM-capabilities-x-channels. Read INV-frozen-surfaces.md before designing anything.

  DONE-CRITERION: The tranche's first artifact names all four DR- ids with the line citations from this report, and states the surface-3 boundary in one sentence.

### E1-1 — Add the CONTAINED backend's own two-armed network differential. New test in tests/test_sandbox_guard.py's OS-layer section (after :554): run a socket probe under `ContainedSimulationBackend.containment_prefix()` and assert connect fails with ENETUNREACH and `socket.if_nameindex()` returns exactly [(1,'lo')]; run the IDENTICAL probe with no prefix and assert its interface list is a strict superset. Skip BOTH arms together when the host itself has only `lo`, so the test can never pass vacuously. This replaces confessions #1 (:146), #4 (:376), #6 (:241) and #10 (:328).

  DONE-CRITERION: `python -m pytest tests/test_sandbox_guard.py -q -k contained_prefix_denies` passes; then monkeypatch `ContainedSimulationBackend._containment_prefix` to `()` (the shape already used at tests/test_contained_simulation_runner.py:153) and confirm the new test goes RED while `_backend().resource_limits()['network'] is False` still holds — that delta IS the proof the differential can fail where the confession cannot.

### E1-2 — Add the contained worker's argv-wiring differential. Monkeypatch `deepreason.verification.contained.subprocess.Popen` with a recorder in the exact shape of tests/test_sandbox_guard.py:496-503, drive `_backend().verify(_request(blobs), blobs)`, and assert `seen[0][:len(prefix)] == list(ContainedSimulationBackend.containment_prefix())` and that the next argv element is `sys.executable`. This replaces confessions #3 (:114), #7 (:242), #8 (:243) and #9 (:327), whose subject is the label `namespace_unshared` — a literal at contained.py:502 that survives any launch that stops applying the prefix.

  DONE-CRITERION: Test passes; mutation proof — edit the recorder to drop the prefix from `seen[0]` (or temporarily assert against a wrong prefix) and confirm RED, then restore. Record both outputs in the tranche's proof/ directory.

### E1-3 — Add the rlimit read-back differential. Spawn a child with `preexec_fn=lambda: _apply_containment_limits(limits)` running `python -c` that prints `resource.getrlimit()` for RLIMIT_NOFILE, RLIMIT_NPROC, RLIMIT_FSIZE, RLIMIT_AS and RLIMIT_CPU as JSON; assert each soft limit equals the corresponding value in `_backend().resource_limits()`. This replaces the self-to-self comparison at tests/test_contained_simulation_runner.py:148-149 and gives NOFILE, NPROC and FSIZE their first effect-observing coverage.

  DONE-CRITERION: Test passes; mutation proof — monkeypatch `_apply_containment_limits` to skip the NOFILE setrlimit and confirm the new test goes RED while lines 148-149's original comparison stays GREEN.

### E1-4 — Replace confessions #2 (:147) and #5 (:377) — the `"ephemeral scratch workdir"` string — with the honest effect pin: using the mkdtemp recorder already at tests/test_contained_simulation_runner.py:196-204 plus the E1-2 Popen recorder, assert the scratch dir is the Popen `cwd=` kwarg, that `HOME` and `TMPDIR` in the captured `env=` both point at it, and that the directory does not exist after `verify()` returns. Do NOT assert the string. Do NOT edit contained.py:519 — see stops.

  DONE-CRITERION: Test passes and the two string assertions at :147 and :377 are gone; `grep -rn 'ephemeral scratch workdir' tests/` returns nothing.

### E1-5 — Record the measurement that the filesystem string over-claims, as a finding rather than a fix. Run the real interpreter under `ContainedSimulationBackend.containment_prefix()` with cwd set to a scratch dir and show it can read `/etc/hostname` — proving no mount namespace, because the prefix carries `--net` only (contained.py:471). Commit the transcript to the tranche's proof/ directory and park the finding against P9's G2, which already names the honest remedy.

  DONE-CRITERION: proof/filesystem_not_a_jail.out exists showing the read succeeding INSIDE the prefix, and the tranche's PARKED.md (or its findings section) carries one entry citing SAFETY.md:397 and PARKED.md:487-491 with no src change made.

### E1-6 — Give the existing one-armed code-testing differential its outside arm. In tests/test_sandbox_guard.py:520-554, run the same probe with no prefix and assert its interface list is a strict superset of ['lo']; guard both arms on the same host condition so neither can pass alone.

  DONE-CRITERION: `python -m pytest tests/test_sandbox_guard.py -q -k network` passes, and the function body contains an assertion on an `outside` result as well as `inside`.

### E1-7 — Pin the two environment scrubs by effect rather than by returned dict. (a) contained: with OLLAMA_API_KEY and DEEPREASON_* set in os.environ, capture the Popen `env=` kwarg and additionally spawn a real child under it that prints `sorted(os.environ)`, asserting neither leaks. (b) code-testing: do the same for `oracle_sandbox._worker_environment()`, which has NO test anywhere today.

  DONE-CRITERION: Two new tests pass; `grep -rn '_worker_environment' tests/*.py` now returns at least one source hit where it previously returned none.

### E1-8 — MAP HALF. Add a `check:` line to docs/map/SUB-verification.md's third Trap (currently ending at :190 with no check), pointing at the new differential tests — e.g. `check: python -m pytest tests/test_sandbox_guard.py -q -k "differential or prefix_denies or rlimit_readback"`. Advance Verified-at only if the document's checks were actually re-run.

  DONE-CRITERION: `python tools/docs_verify.py` shows the new check passing, and `python tools/docs_verify.py --audit` does NOT refuse it (a check that cannot fail is refused — prove it can by temporarily renaming one target test and seeing the check go red).

### E1-9 — Ring-gate E1, then boundary-gate. Iterate with the three affected files only; run the full gate once at the phase boundary.

  DONE-CRITERION: `python -m pytest tests/test_sandbox_guard.py tests/test_contained_simulation_runner.py tests/test_simulation_runner_default.py -q` → 0 failed; then `python -m pytest tests/ -q -n 4` → 0 failed, re-running serially any of the five known-flaky tests named at docs/AUDIT_BASELINES.md:22-24.

### E2-1 — CLAUDE.md edit (a), Environment section. BEFORE (CLAUDE.md:130-133):
    git log --oneline -1        # stale head? resync:
    git fetch origin <branch> && git checkout -B <branch> origin/<branch>
    which deepreason || pip install -e . --break-system-packages -q
    ls experiments/live_research_*/env   # gitignored credential file
AFTER:
    git log --oneline -1        # stale head? resync:
    git fetch origin <branch> && git checkout -B <branch> origin/<branch>
    which deepreason || pip install -e . --break-system-packages -q
    python -m pip install pytest pytest-xdist jsonschema \
        --break-system-packages -q   # the GATE's deps; pyproject declares none
    ls experiments/live_research_*/env   # gitignored credential file
Plus one prose paragraph immediately after line 139 stating: pyproject.toml declares pydantic, pyyaml and fastembed (:11-21) and a dev extra of pytest and ruff (:23-27); the documented gate additionally needs pytest-xdist (for -n 4) and jsonschema (tests/test_schema_carries_every_prose_rule.py:170), and a fresh container that runs only the documented install gets one failure that looks like a code defect and is not (experiments/2026-08-27-change-execution-safety/DELIVERY.md:127-152). Point at docs/AUDIT_BASELINES.md:49-56, which already carries the exact remedy line.

  DONE-CRITERION: `sed -n '125,150p' CLAUDE.md` shows both the added install line and the paragraph; `grep -c 'pytest-xdist' CLAUDE.md` >= 1; `grep -c 'jsonschema' CLAUDE.md` >= 1.

### E2-2 — CLAUDE.md edit (b), Build and test. BEFORE (CLAUDE.md:159-162):
    pip install -e . --break-system-packages    # editable install; the
                                                # CLI and live runs share it
    pytest tests/ -q -n 4                       # full gate, ~8 min
                                                # expect ~3100 passed, 0 failed
AFTER:
    pip install -e . --break-system-packages    # editable install; the
                                                # CLI and live runs share it
    python -m pip install pytest pytest-xdist jsonschema \
        --break-system-packages                 # the gate's own deps —
                                                # NOT declared in pyproject
    pytest tests/ -q -n 4                       # full gate, ~14 min
                                                # 0 failed is the baseline; the
                                                # passed count moves every
                                                # tranche — docs/AUDIT_BASELINES.md
                                                # is the living source
Note both stale values are corrected: '~3100 passed' (4491 collected today) and '~8 min' (three recorded runs: 13:43, 14:35, 16:34).

  DONE-CRITERION: `grep -n '3100' CLAUDE.md` returns nothing; `grep -n 'AUDIT_BASELINES' CLAUDE.md` returns at least one hit inside the Build-and-test section; `sed -n '157,175p' CLAUDE.md` reads as the AFTER block.

### E2-3 — OPTIONAL, and only if the boundary gate was actually run in this tranche: record the freshly measured passed/skipped count in docs/AUDIT_BASELINES.md's full-gate bullet (:14-24), beside the existing '0 failed', with the date and commit. Do NOT write a number the tranche did not measure — collection count (4491) is not a run count.

  DONE-CRITERION: If done: docs/AUDIT_BASELINES.md:14-24 names a passed count with the date and the commit that measured it. If skipped: the tranche's delivery artifact says explicitly that the count was left to '0 failed' because no full-gate number was measured.

### E2-4 — Gate the doc edits. CLAUDE.md carries no docs_verify checks itself, but run docs_verify anyway to confirm nothing regressed, and compare against the documented expected-failure list.

  DONE-CRITERION: `python tools/docs_verify.py` matches docs/AUDIT_BASELINES.md:25-47 exactly — 6 failed on a full clone, 9 on a shallow one, with the same six rows; any delta is a finding, not a pass.


## Risks

- A skipped differential must never read as a pass. `@needs_containment` / `pytest.skip` on a host without user namespaces silently converts every new E1 test into no evidence at all. Every new differential must be TWO-ARMED and both arms guarded on the same condition, so it either measures a difference or reports skipped — never passes on one arm. The existing test at tests/test_sandbox_guard.py:553-554 is the counterexample already in the tree.
- Deleting `receipt.resource_limits['network'] is False` outright would weaken a coupling verify_root actually consumes (src/deepreason/invariants.py:1854). Keep ONE assertion that the receipt CARRIES the field replay validation reads, and pair it with the E1-1/E1-2 differentials so the field's truth is measured rather than confessed. Report the pairing explicitly so a later reader does not mistake the surviving assertion for a leftover confession.
- E1-5 produces a measurement that CONTRADICTS a committed string. Under P4's own scope rule that is a finding for a defect tranche, not a fix — but a reader who sees the transcript without the framing will read it as a live escape. It is not: the language boundary denies `open` at all five call sites (tests/test_sandbox_guard.py:318-379), so nothing model code can express reaches the filesystem. The transcript must carry that sentence beside it.
- The contained backend and the code-testing channel run DUPLICATED probes (contained.py:457-487 vs sandbox_os.py:54-83), and sandbox_os.py:16-19 documents a single shared probe that does not exist. Differentials written against one prefix say nothing about the other. Each differential must name which backend's prefix it exercised; do not generalize from `sandbox_os.network_denial_prefix()` to `ContainedSimulationBackend.containment_prefix()`.
- Both probes cache per process (contained.py:466-467, sandbox_os.py:61-63). A test that monkeypatches `_containment_prefix` and another that reads the real one can interfere under `-n 4` if either forgets to restore. Use monkeypatch (which restores) and `sandbox_os.reset_probe_cache()` (sandbox_os.py:90-94) rather than assigning module globals directly.
- New tests spawn real subprocesses under `unshare`. Under `-n 4` that multiplies wall time and can surface the five known-flaky thread-join tests (docs/AUDIT_BASELINES.md:22-24). Budget ~14 min for the boundary gate, and re-run any flake serially before calling it a regression.
- E2's claim cannot be reproduced in THIS container: jsonschema 4.26.0 and xdist 3.8.0 are both already installed (measured). The claim must be argued from pyproject.toml:11-27 and DELIVERY.md:127-152 — do not attempt a live ModuleNotFoundError here, and do not uninstall anything to manufacture one.
- Any passed-count literal written into CLAUDE.md is stale on arrival: 4334 (2026-08-27), 4364, 4374 (2026-08-28), 4491 collected today. That is precisely why E2-2 points at docs/AUDIT_BASELINES.md instead of writing a new number. Resist the temptation to 'just update it to 4491' — a collection count is not a run count.
- docs/AUDIT_BASELINES.md's full-gate bullet currently has NO passed count. If CLAUDE.md says 'the living count is there' and it is not, the pointer dangles. Either phrase the pointer as '0 failed is the baseline; AUDIT_BASELINES.md is the living source' (accurate today), or do E2-3 and put a measured number there in the same commit.
- P6's own prompt asks for the pyproject.toml declaration, which this lane's scope excludes. If the lane ships only the doc edit, the delivery artifact must say plainly that P6 is PARTIALLY discharged — the gap is documented, not closed — so the park is not marked done on a half.

## Stops (bubble, never resolve in-batch)

- Any edit to src/deepreason/verification/contained.py is a STOP. It is inside frozen surface 3 (docs/map/INV-frozen-surfaces.md:47-53, 'Replay-validation record formats — invariants.py, verification/'). This bites in three specific places the lane will be tempted by: (a) correcting or removing the false `"filesystem": "ephemeral scratch workdir"` literal at contained.py:519; (b) making `resource_limits()` consult `containment_prefix()` so `"network": False` could ever go true; (c) deduplicating the probe at contained.py:457-487 against sandbox_os.py. All three are the RIGHT fixes and NONE of them belongs in this lane — (a) and (b) are already parked as P9/G2, and (c) is new. Bubble each as a finding with a written frozen-surface grant request, per the discipline INV-frozen-surfaces.md records for the 2026-08-25 and 2026-08-27 grants; the monitor reviews it in FIX.md, not in chat.
- Any edit to src/deepreason/oracle_sandbox.py is a STOP for this lane — not because it is frozen (it is NOT), but because P4's own scope sentence is 'tests/ only, plus whatever docs/map check makes the standard enforceable. No src changes' (PARKED.md:236-238). If a differential on the code-testing channel goes RED, that is a defect tranche, not a fix here.
- Any edit to src/deepreason/invariants.py is a STOP — frozen surface 3, and line 1854's consumption of `resource_limits['network']` is exactly the kind of reader a differential tranche must leave alone.
- E2's scope is docs. Editing pyproject.toml to declare jsonschema and pytest-xdist — which P6's own prompt asks for at PARKED.md:311-315 — is OUT of this lane as briefed, even though pyproject.toml is not frozen. Bubble it: the parent must decide whether E2 ships the doc half only (P6 partially discharged) or is widened to close the declaration too. Recommend widening, because the census is already done and is small: jsonschema is the ONLY undeclared third-party test import in the whole suite, and pytest-xdist is not an import at all.
- Deleting the redundant bare `import jsonschema` at tests/test_schema_carries_every_prose_rule.py:170 — which defeats the `pytest.importorskip` twelve lines below at :182 and is, by itself, a complete fix for the observed gate failure — is a tests/ edit, so it sits inside E1's scope and outside E2's docs-only scope. This is a genuine fork the parent must settle, not something to resolve in-batch: road A documents the gap (E2 as briefed), road B declares the dependency (pyproject), road C removes the need for it (one deleted line). They are not mutually exclusive and B+C together make the documentation in A merely historical. Bubble with all three priced.
- If E1-5's measurement is read as authorizing a src correction to the filesystem string 'while we are here', STOP. That is frozen surface 3 and is already parked as P9. The measurement's only in-lane product is a transcript and a parked finding.
