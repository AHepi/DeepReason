# RECON-D — Lane D — the four rotted map checks (docs/map + measurement only; no src/ changes)

Read-only reconnaissance, batch 2, produced before any lane work. Every claim cites file:line.

## Summary

Lane D repairs four map claims/checks that the 2026-08-29 multi-line-parser fix executed for the first time, and it repairs them in `docs/map/` only. D1: the `llm × verification` seam's core claim ("no import in either direction") is FALSE in one direction — verification imports llm at SEVEN (file, module, symbol) crossings across six import statements (one module-level, five function-local, spanning `invariants.py` and `verification/report.py`); the reverse direction is genuinely ZERO. The code is frozen and stays untouched: the DOCUMENT is corrected, and two sibling documents (`SUB-verification.md`, `INDEX.md`) repeat the same false sentence and must move in the same commit. D2: the qualification-subject digest pin at `INV-frozen-surfaces.md:734` asserts `b9038b84…`; the tree measures `02ee7e09…`. The digest genuinely MOVED, on 2026-08-28, in commit `e9457f8ff` (tranche `experiments/2026-08-27-change-execution-safety/`) under the operator's conditional frozen-surface grant, and the two committed TEST pins were updated while this dark map pin was not. Every OTHER pin in that file measures as asserted — verified by running each — so no other-pin STOP fires. D3: `CON-discharge-channel.md:150` dies before either assertion because its fixture binds `engaged_local_simulation_toolchain()` against a policy that names the CONTAINED toolchain; swapping one symbol to `engaged_simulation_toolchain()` makes it compile AND pass — which exposes a second, larger finding: the surrounding prose still says the FREE layer is "reachable only by editing code", and lane B2's carriage fix (commit `9a7b0a625`) made that false. D4: `INV-signal-contract.md:243` is defeated by a COMMENT at `scheduler/scheduler.py:1132`; an `ast.unparse` rewrite is verified green today and verified RED under a planted regression. Current full `docs_verify`: 70 documents, 1248 checks, 9 failed — exactly the shallow-clone baseline, delta ZERO.

## Facts

- **FINDINGS.md class (b) is four items, all newly executed, none in that tranche's cone.**
  - experiments/2026-08-29-fix-docs-verify-multiline-checks/FINDINGS.md:32 — "## Class (b) — the claim rotted (4, all newly executed, none in this cone)"

- **B1 states the seam claim verbatim and names five import sites in invariants.py.**
  - experiments/2026-08-29-fix-docs-verify-multiline-checks/FINDINGS.md:36-48 — "Claim it defends, verbatim: \"Between them there is **no import in either direction** — `invariants.py` names nothing from `llm/`, and `llm/` names nothing from `invariants.py`.\" … `src/deepreason/invariants.py:21` is a module-level `from deepreason.llm.firewall import route_fingerprint`, with four more function-local `deepreason.llm.*` imports at lines 1214, 1215, 1260 and 4101. The direction the seam denies exists five times over. … This is the most load-bearing failure in the table."

- **B2 states the pin disagrees with the same document's other pin, and that the surface has NOT drifted — only the pin is stale.**
  - experiments/2026-08-29-fix-docs-verify-multiline-checks/FINDINGS.md:63-68 — "The same document pins the same expression twice, at :533 and at :657, with two different values. :533 is right and :657 is stale. Both were dark, so nothing could ever have made them argue. The digest itself has not silently drifted — the current value is the one :533 asserts — so this is a stale pin, not a broken surface. It still has to be corrected by someone with the surface-5 authority to touch that document."

- **B3 locates the D3 fixture bug: local toolchain bound against a policy naming the contained one; the claim is unreached, not disproven.**
  - experiments/2026-08-29-fix-docs-verify-multiline-checks/FINDINGS.md:88-92 — "engaged_local_simulation_toolchain().id = python@deepreason-public-local.v1 / The check binds the LOCAL toolchain against a policy that names the CONTAINED one. The claim about `DISCHARGE_POLICY` is untested either way — it is not shown false, it is unreached."

- **B4 names the comment and prescribes the repair technique.**
  - experiments/2026-08-29-fix-docs-verify-multiline-checks/FINDINGS.md:104-111 — "The single occurrence is `scheduler/scheduler.py:1127`, and it is a COMMENT … `inspect.getsource` returns comments, so a sentence explaining the decoupling trips the check that proves it. On the evidence the claim still holds and the CHECK is what needs the fix (parse the AST, or scan `ast.unparse` output, rather than raw source text)."

- **FINDINGS.md records the honest totals as 6 failed full-clone / 9 shallow, both baselined.**
  - experiments/2026-08-29-fix-docs-verify-multiline-checks/FINDINGS.md:181-184 — "So the honest totals are **6 failed on a full clone, 9 on a shallow one**, and both are recorded in `docs/AUDIT_BASELINES.md` rather than one being presented as the truth."

- **SCHEMA.md: a check must start at column 0 and is an inline-code span.**
  - docs/map/SCHEMA.md:90-91 — "A check must start at **column 0** — that is what lets the worked examples above sit inside an indented block without the verifier trying to run them."

- **SCHEMA.md: the multi-line form opens with a column-0 `check:` span and closes at the first later line whose text ends with a backtick; newlines are part of the command.**
  - docs/map/SCHEMA.md:93-95 — "A check MAY SPAN SEVERAL LINES. It opens with a `check:` span at column 0 and closes at the first later line whose text ends with a backtick. The newlines between are part of the command, so a `python -c` body keeps its statements"

- **SCHEMA.md: the grammar is TOTAL — a column-0 opener is a check or an ERROR, never prose; never begin a line with a quoted check: span you do not mean to run.**
  - docs/map/SCHEMA.md:105-117 — "The grammar is TOTAL: at column 0, `check:` opens a check or an ERROR — never prose. … The price of totality is one authoring rule: **never begin a line with a quoted `check:` span you do not mean to run.** Wrap the sentence so the span sits mid-line, or indent it."

- **SCHEMA.md: use `python -m pytest`, never bare `pytest`, inside a check.**
  - docs/map/SCHEMA.md:126-128 — "Use `python -m pytest`, never bare `pytest`: the container's PATH may resolve `pytest` to a tool shim that cannot see the editable install, which fails a check for a reason that has nothing to do with the claim."

- **SCHEMA.md check-writing rule 3 is exactly the D4 technique: resolve imports/names via AST, not substring greps.**
  - docs/map/SCHEMA.md:168-170 — "3. **Substring import greps miss relative imports.** `from ..rules.spawn import …` walked past `deepreason.rules` greps, including on a seam's core dependency-arrow claim. Resolve `ImportFrom` levels via AST."

- **SCHEMA.md check-writing rule 6: when the prose states a number, the check pins it with -eq.**
  - docs/map/SCHEMA.md:178-179 — "6. **Counts are claims.** `-ge N` floors hid a 6-file error and a 28-vs-29 mismatch; when the prose states a number, the check pins it with `-eq`."

- **SCHEMA.md: Verified-at is advanced only if the document's checks were actually re-run; a stale stamp is honest, a false one is not.**
  - docs/map/SCHEMA.md:269-272 — "2. **Update `Verified-at:`** to the commit you are making. If you did not check the document's claims, do not advance the stamp — a stale stamp is honest, a false one is not."

- **SCHEMA.md: a Traps entry is never deleted, only rewritten to say it was fixed and when.**
  - docs/map/SCHEMA.md:288-290 — "7. **Never delete a `Traps` entry** because the trap was fixed. Rewrite it to say it was fixed and when. Traps are the memory of what has actually gone wrong, and that memory is the most expensive content here to regenerate."

- **SCHEMA.md: a seam without a Sweep: header MUST gain one the next time the document is edited.**
  - docs/map/SCHEMA.md:318-320 — "The header ratchets in: a seam without one is reported by `--coverage` but not failed, and MUST gain one the next time the document is edited."

- **SCHEMA.md: a Sweep: header must target ENFORCEMENT, and when every candidate flags only readers, leave the header off and say why in the body.**
  - docs/map/SCHEMA.md:186-189 — "A `Sweep:` header must target ENFORCEMENT (sites that compare or raise on the field), not readers. When every candidate spec flags only readers — it happens; `SEAM-evaluation-x-ontology` is the recorded case — leave the header off and say why in the body rather than shipping a spec that cries wolf."

- **SCHEMA.md forbids line numbers in prose.**
  - docs/map/SCHEMA.md:358-359 — "- Line numbers in prose. They rot within days. Name the function or the symbol; `grep` is the address."

- **SCHEMA.md's own self-test check asserts at least 70 multi-line checks exist map-wide.**
  - docs/map/SCHEMA.md:119-124 — "`check: python tools/docs_verify.py --self-test && python -c \"…multi = [(d.path.name, n) for d in dv.documents() for n, c in d.checks if '\\n' in c]\nassert len(multi) >= 70, len(multi)\n\"`"

- **docs_verify parses a single-line check with _CHECK and every column-0 opener with _CHECK_OPEN; the two are deliberately split.**
  - tools/docs_verify.py:59-67 — "_CHECK = re.compile(r\"^`check:\\s*(?P<cmd>.+?)`\\s*$\") … _CHECK_OPEN = re.compile(r\"^`check:\")"

- **_read_block consumes a multi-line check, strips the opener prefix and the closing backtick, preserves newlines, and records the OPENER line number (start+1).**
  - tools/docs_verify.py:106-115 — "while end < len(lines) and not _CHECK_OPEN.match(lines[end]): if lines[end].rstrip().endswith(\"`\"): block = lines[start:end + 1]; block[0] = block[0][len(\"`check:\"):]; block[-1] = block[-1].rstrip()[:-1]; doc.checks.append((start + 1, \"\\n\".join(block).strip())) … doc.errors.append((start + 1, _UNPARSEABLE.format(opener=lines[start][:100])))"

- **Every check is executed as a shell command from the repo root with a 300 s timeout; exit 0 is the only pass.**
  - tools/docs_verify.py:196-209 — "proc = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True, text=True, timeout=CHECK_TIMEOUT_S,)" and tools/docs_verify.py:185 — "CHECK_TIMEOUT_S = 300"

- **Default (full) mode ignores the cache entirely; only --fast/--failed read it.**
  - tools/docs_verify.py:218 — "cache = _load_cache() if (fast or only_failed) else {}"

- **--audit's vacuous detection is a static regex over the command's leading token, matching only true/:/echo/test -efd PATH/ls PATH.**
  - tools/docs_verify.py:78-80 — "_VACUOUS = re.compile(r\"^\\s*(true|:|echo\\b|test\\s+-[efd]\\s+\\S+\\s*$|ls\\s+\\S+\\s*$)\", re.IGNORECASE)"

- **cmd_audit applies _VACUOUS per check, and also reports documents with no checks and every unparseable opener; that loop is the only place to add a new lint.**
  - tools/docs_verify.py:441-451 — "for doc in documents(): if not doc.checks and doc.doc_id not in {\"DR-SCHEMA\", \"DR-INDEX\"}: … for number, problem in doc.errors: … for number, cmd in doc.checks: if _VACUOUS.match(cmd): print(f\"{doc.path.name}:{number}: vacuous check `{_render(cmd)}`\")"

- **docs_verify.py has no tests/ coverage; --self-test is its only gate, so any new --audit lint must be pinned there.**
  - tools/docs_verify.py:459-461 — "This is the tool's own gate: nothing in tests/ exercises it, so every grammar rule SCHEMA.md states is pinned here, in both directions"

- **SCHEMA.md's description of --audit is FALSE against the code: --audit never mutates or executes anything.**
  - docs/map/SCHEMA.md:193-194 — "`tools/docs_verify.py --audit` flags checks that pass against a deliberately mutated tree." — contradicted by tools/docs_verify.py:439 "\"\"\"Flag checks that cannot fail, and documents with no checks at all.\"\"\"" whose only test is the static `_VACUOUS.match(cmd)` at :449

- **AUDIT_BASELINES.md is read by the audit family as PRECEDENCE 2 and moves only in a non-audit tranche, in the same commit as whatever moved the value.**
  - docs/AUDIT_BASELINES.md:3-8 — "Read by the dr-audit family (PRECEDENCE 2): a delta from these values is a finding; a match is disposition `baseline`. This file moves only in a non-audit tranche, in the same commit as whatever moved the value, with the audit family's close gate re-run there. A baseline believed wrong during an audit is rowed and parked, never edited mid-audit."

- **AUDIT_BASELINES.md's docs_verify baseline is 1212 checks over 69 documents, 6 failed full clone / 9 shallow, re-baselined 2026-08-29.**
  - docs/AUDIT_BASELINES.md:25-29 — "- **docs_verify** (`python tools/docs_verify.py`): **1212 checks over 69 documents; 6 failed on a full clone, 9 on a shallow one.** Re-baselined 2026-08-29"

- **AUDIT_BASELINES.md's expected-failure table names all six by document:line, and its line numbers are now STALE for three rows.**
  - docs/AUDIT_BASELINES.md:36-41 — "| `SEAM-llm-x-verification.md:19` … | `INV-frozen-surfaces.md:657` … | `SEAM-llm-x-rules.md:54` … | `INV-signal-contract.md:222` … | `CON-discharge-channel.md:150` … | `INV-frozen-surfaces.md:181` …" (measured today: the pin is at :734 and the signal-contract check at :243)

- **AUDIT_BASELINES.md names the three shallow-clone-only failures and says they are not findings on a shallow container.**
  - docs/AUDIT_BASELINES.md:43-47 — "Plus, on a SHALLOW clone only, 3 more: `CON-run-identity.md:200`, `:202`, `:204` are git-history checks that need the full history. All three PASS after `git fetch --unshallow` … A container that reports `git rev-parse --is-shallow-repository` as `true` will show 9, not 6, and those 3 are not findings."

- **This container IS shallow, so 9 is the correct baseline here.**
  - measured: `git rev-parse --is-shallow-repository` → `true`; oldest reachable commit is `2bc7cfef9 2026-08-27 audit part 1: kind-signal sweep instruments + raw site list` (163 commits total)

- **AUDIT_BASELINES.md's environment warning about the interpreter split is satisfied on this container.**
  - docs/AUDIT_BASELINES.md:49-56 — "ENVIRONMENT, or the number is meaningless … Run `python -m pip install -e . pytest pytest-xdist jsonschema --break-system-packages` and confirm `python -m pytest --version` before trusting any docs_verify total." — measured: `which python` → /usr/local/bin/python; `python -m pytest --version` → pytest 9.1.1; `python -c 'import deepreason'` → /home/user/DeepReason/src/deepreason/__init__.py

- **D1 — the seam's core claim, verbatim, as committed today.**
  - docs/map/SEAM-llm-x-verification.md:12-17 — "`DR-SUB-llm` WRITES provider evidence. `DR-SUB-verification` READS it back and decides whether the run is replayable. Between them there is **no import in either direction** — `invariants.py` names nothing from `llm/`, and `llm/` names nothing from `invariants.py`."

- **D1 — the failing check, verbatim, is a multi-line AST block covering only invariants.py and llm/adapter.py.**
  - docs/map/SEAM-llm-x-verification.md:19-32 — "`check: python -c \"\nimport ast, pathlib\nfor path, forbidden in (\n    ('src/deepreason/invariants.py', 'deepreason.llm'),\n    ('src/deepreason/llm/adapter.py', 'deepreason.invariants'),\n): …"

- **D1 — verification -> llm crossing 1 of 6: module-level, frozen surface 3 importing the frozen-ADJACENT symbol.**
  - src/deepreason/invariants.py:21 — "from deepreason.llm.firewall import route_fingerprint"

- **D1 — crossing 2 of 6: function-local inside verify_root.**
  - src/deepreason/invariants.py:1214 — "                    from deepreason.llm.contracts import ConjecturerOutput"

- **D1 — crossing 3 of 6: function-local inside verify_root, two names (AliasTable, wire_contract_for).**
  - src/deepreason/invariants.py:1215-1218 — "                    from deepreason.llm.wire import (\n                        AliasTable,\n                        wire_contract_for,\n                    )"

- **D1 — crossing 4 of 6: function-local inside verify_root, the Mini reference-free contract.**
  - src/deepreason/invariants.py:1260-1262 — "                        from deepreason.llm.wire import (\n                            ReferenceFreeConjecturerWireContract,\n                        )"

- **D1 — crossing 5 of 6: function-local inside verify_root, for the detection-total check.**
  - src/deepreason/invariants.py:4101 — "        from deepreason.llm.embedder import HashingEmbedder" (used at :4103 "        raw_flags(h, HashingEmbedder(), Config())")

- **D1 — crossing 6 of 6, MISSED BY FINDINGS.md: a second verification-side importer outside invariants.py.**
  - src/deepreason/verification/report.py:721 — "    from deepreason.llm.firewall import route_fingerprint" (inside `_transaction_findings`, defined at :711; used at :767 "            if lease.route_sha256 != route_fingerprint(route):")

- **D1 — the reverse direction is genuinely ZERO in every form (absolute, relative, plain import), across all of src/deepreason/llm/.**
  - measured by AST over all 18 files of src/deepreason/llm/ for prefixes 'deepreason.invariants', 'deepreason.verification', 'deepreason.signals_read': 0 hits each; the only textual match anywhere is a comment, src/deepreason/llm/adapter.py:947 — "            # verification."

- **D1 — the llm/adapter.py half of the seam check passes on its own; only the invariants.py half fails.**
  - measured: running the seam check's llm/adapter.py leg alone prints "llm/adapter.py half of the seam check: PASSES"; the full check fails with "AssertionError: ('src/deepreason/invariants.py', 'deepreason.llm.firewall')"

- **D1 — the seam's Traps entry repeats the false claim and must be rewritten (not deleted).**
  - docs/map/SEAM-llm-x-verification.md:163-165 — "- **Zero import traffic is not zero coupling.** This pair carries no import in either direction and therefore never appeared in `INDEX.md`'s matrix, which is built from measured coupling."

- **D1 — the same false claim is repeated in INDEX.md's unchecked prose.**
  - docs/map/INDEX.md:150-152 — "The llm × verification case is the newest and cost the most: the two sides import NOTHING from each other in either direction, so the pair was absent from this matrix entirely — which reads as \"no interaction\" and is not."

- **D1 — SUB-verification.md labels the pair 'deliberately absent'; only its stated evidence (the llm side) survives.**
  - docs/map/SUB-verification.md:19 — "| llm x verification | **deliberately absent** | confirmed from the llm side: `llm/`'s own check proves it never imports `verification` |"

- **D1 — what actually polices the boundary, part 1: SUB-llm.md's grep check, which is GREEN but does NOT cover deepreason.invariants.**
  - docs/map/SUB-llm.md:27 — "`check: ! grep -rqE \"^[[:space:]]*(from|import) +deepreason\\.(harness|scheduler|rules|adjudication|capture|informal|verification|amendment)\\b\" src/deepreason/llm/ --include=*.py && …" — measured exit 0; and `echo "from deepreason.invariants import verify_root" | grep -qE …` → NOT COVERED

- **D1 — what actually polices the boundary, part 2: nothing in tests/. No pytest test asserts either direction.**
  - measured: no test file in tests/ contains an llm↔verification import-boundary assertion; `grep -rn "route_fingerprint" tests/` returns only ordinary call-site uses (e.g. tests/test_run_manifest.py:30 "from deepreason.llm.firewall import route_fingerprint"). The only enforcement is the two map checks above.

- **D1 — route_fingerprint is a repo-wide shared identity function, not a seam-local leak: 15 src modules import it.**
  - measured `grep -rn route_fingerprint src/`: importers include src/deepreason/run_manifest.py:1795, src/deepreason/rules/crit.py:28, src/deepreason/scheduler/scheduler.py:27, src/deepreason/workflow/replay.py:1027, src/deepreason/scratch/authoring.py:17, src/deepreason/invariants.py:21, src/deepreason/verification/report.py:721; defined at src/deepreason/llm/firewall.py:115 "def route_fingerprint(route: Route) -> str:"

- **D1 — a candidate replacement check that pins the exact crossing set in both directions PASSES today.**
  - verified in /tmp/…/scratchpad/d1check.py: AST over invariants.py + verification/**.py asserts `forward` equals exactly 7 (file, module, symbol) triples and `back` (llm/ → deepreason.invariants|deepreason.verification) equals the empty set → "D1 candidate check PASSES; crossings pinned: 7"

- **D2 — the stale pin, verbatim, at its CURRENT location.**
  - docs/map/INV-frozen-surfaces.md:734-742 — "`check: python -c \"\nimport json\nfrom tests.test_reusable_qualification import _manifest, _profile\nfrom deepreason.qualification import qualification_subject_digest\np = _profile()\nassert qualification_subject_digest(_manifest(p), p) == 'b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386'\nleaked = sorted(k for k in json.loads(_manifest(p).engine_config_json) if k == 'DISCHARGE_POLICY')\nassert not leaked, leaked\n\"`"

- **D2 — running that check's own command reproduces the failure, and the actual value is 02ee7e09…**
  - measured: the pin command exits 1 with `AssertionError` at line 6; `qualification_subject_digest(_manifest(_profile()), _profile())` prints `02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713`; the DISCHARGE_POLICY-leak half of the same check is satisfied (`DISCHARGE_POLICY leaked: []`)

- **D2 — the correct pin, at its CURRENT location, asserts the value the tree produces and PASSES.**
  - docs/map/INV-frozen-surfaces.md:615 — "assert base == '02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713', base" — the whole check at :610-622 measured exit 0

- **D2 — the surrounding prose says this check exists to prove the F1 DISCHARGE_POLICY contact left surface 5 at zero.**
  - docs/map/INV-frozen-surfaces.md:714-719 — "Surface 5 stayed at ZERO for the tranche's other half too, and that is measured rather than assumed: the channel adds two optional wire fields … so the subject digest over a committed fixture is unchanged at `b9038b84efdea313…`."

- **D2 — the digest DID move, and the commit says so in its own body: this is the finding PARKED P2 said must go to the operator.**
  - git commit e9457f8ff (2026-08-28) "switch on: the container profile serves BOTH simulation modes, not one" body — "Both digest pins moved for the reason they exist to detect … \n    f3bb6562...  ->  83454b08...   (shipped qualification subject)\n    b9038b84...  ->  02ee7e09...   (discharge-wire subject)\n\nThis is the C6 cost landing where it was priced: the first live run after this pays a fresh qualification battery (~14 min, ~1160 calls)."

- **D2 — the tranche that owns that commit is the execution-safety tranche.**
  - experiments/2026-08-27-change-execution-safety/DELIVERY.md:386-393 — "The compiled manifest changed, and the manifest is part of the qualification behavior subject, so **the first live run after this pays a fresh qualification battery** (~14 min, ~1160 calls). Two committed digest pins moved to match … f3bb6562...  ->  83454b08...   shipped qualification subject / b9038b84...  ->  02ee7e09...   discharge-wire subject"

- **D2 — the grant that authorized it, in the operator's verbatim words.**
  - experiments/2026-08-27-change-execution-safety/REQUEST.md:155-157 — "Operator, verbatim:\n\n> can you fix please. Frozen surface changes are permitted as long as you\n> document what is affected." and :165-175 "**C7 (constraint): frozen surfaces are GRANTED, conditional on documentation.** … recorded in FIX.md BEFORE implementation and in `docs/map/INV-frozen-surfaces.md` as a granted contact"

- **D2 — the two committed TEST pins were updated in that commit; the map's dark pin was not.**
  - tests/test_discharge_wire.py:197-206 — "The constant moved on 2026-08-28 (execution-safety tranche) because the MANIFEST half changed … the default simulation runner became the contained one, so the compiled policy binds `python@deepreason-public-contained.v1` … \n\n        b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386  before\n        02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713  after"; the map pin at INV-frozen-surfaces.md:739 still reads b9038b84

- **D2 — the 2026-08-28 P10 tranche's own measurement table already records 02ee7e09 as the base, confirming the move predates it.**
  - docs/map/INV-frozen-surfaces.md:594-599 — "config                                       base          without the grant   WITH it\ndefault                                      02ee7e098bb9  02ee7e098bb92390    identical"

- **D2 — batch 1 already measured this pin on both trees and concluded carriage moved nothing.**
  - experiments/2026-08-29-ultracode-batch-1/BATCH.md:491-500 — "    this branch : 02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713\n    main        : 02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713\n    the pin says: b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386\n\nByte-identical to `main`. The pin was already wrong before this branch existed, and **carriage moved nothing**."

- **D2 — EVERY OTHER pin in INV-frozen-surfaces.md measures as asserted; only :734 and the pre-existing :181 census fail.**
  - measured individually, all exit 0: :347 (SPLIT_BUDGET pops -eq 2), :525 (6c2d01f6 source_config_hash + carriage), :610 (02ee7e09 + payload exclusion), :623 (061efe5b + ENGINE_CONFIG_FIELD_NOT_CARRIED -eq 1), :659 (SPLIT_BUDGET_SEAT_PROTOCOL pop), :673 (K_FRAME/PROMOTION_ENVIRONMENT_MAX), :721 (DISCHARGE_POLICY pop at exact indent), :727 (6c2d01f6 / 2624603035 by schema version), :297 (branch tripwire). :181 exits 1 (baseline). The authoritative full run agrees: the only INV-frozen-surfaces failures are :181 and :734.

- **D2 — the complete inventory of hex digest pins in that file, and their verdicts.**
  - docs/map/INV-frozen-surfaces.md — :536 and :731 pin `6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81` (PASS); :732 pins `2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5` (PASS); :615 pins `02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713` (PASS); :629 pins `061efe5bdf7eb5654c569dfab134efd47c88be0eb18134012242c295a653d754` (PASS); :739 pins `b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386` (FAIL). Prose-only mentions (no check) at :342, :409-411, :654, :706, :719 are historical statements about past tranches.

- **D3 — the check's current text, verbatim, including the assertion lane B2 already inverted.**
  - docs/map/CON-discharge-channel.md:150-160 — "`check: python -c \"\n…from deepreason.v6_policy import engaged_control_plane_policy_v3, engaged_inquiry_capability_policy, engaged_local_simulation_toolchain\n…toolchains=(engaged_local_simulation_toolchain(),), inquiry_capability_policy=engaged_inquiry_capability_policy(attached_evidence=False), run_input_digest='0'*64)\nassert 'DISCHARGE_POLICY' not in json.loads(m.engine_config_json)\nassert config_from_run_manifest(m).DISCHARGE_POLICY == 'off', 'carriage no longer restores the configured value -- P15 may have regressed; re-read this section'\n\"`"

- **D3 — running it reproduces the exact failure, before either assertion.**
  - measured: `pydantic_core._pydantic_core.ValidationError: 1 validation error for RunManifest / Value error, V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain`, raised from src/deepreason/run_manifest.py:4023 inside `compile_run_manifest`

- **D3 — the validator that rejects it requires exactly one toolchain whose id equals the policy's identity.**
  - src/deepreason/run_manifest.py:3598-3606 — "    matches = tuple(\n        toolchain\n        for toolchain in manifest.toolchains\n        if toolchain.id == policy.python_toolchain_identity\n    )\n    if len(matches) != 1:\n        raise ValueError(\n            \"V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain\"\n        )"

- **D3 — the exact mismatch, measured today.**
  - measured: `engaged_inquiry_capability_policy(attached_evidence=False).simulation.python_toolchain_identity` → `python@deepreason-public-contained.v1`; `.runner_profile` → `simulation.container.v1`; `engaged_local_simulation_toolchain().id` → `python@deepreason-public-local.v1`

- **D3 — the repair is a one-symbol swap to the policy-tracking factory, which already exists.**
  - src/deepreason/v6_policy.py:680-685 — "def engaged_simulation_toolchain(environ=None) -> ToolchainEntry:\n    \"\"\"Return the one frozen toolchain matching the engaged simulation policy.\"\"\"\n\n    if _contained_runner_opted(environ):\n        return engaged_contained_simulation_toolchain()\n    return engaged_local_simulation_toolchain()"

- **D3 — with that swap the check COMPILES and both assertions PASS.**
  - measured with `toolchains=(engaged_simulation_toolchain(),)`: "compiled OK / DISCHARGE_POLICY in engine_config_json: False / config_from_run_manifest(m).DISCHARGE_POLICY = 'off' / compile_notices: [('ENGINE_CONFIG_FIELD_NOT_CARRIED', '/engine_config/DISCHARGE_POLICY')]"

- **D3 — SECOND FINDING: the prose the check defends is now false. It says the FREE layer is reachable only by editing code, which carriage disproved.**
  - docs/map/CON-discharge-channel.md:133-148 — "**The default is the ONLY road, and that is a defect, not a design.** … The one run path … then rebuilds Config with `config_from_run_manifest`, so the field falls back to its CODE DEFAULT and a YAML line naming a preset is inert. … The consequence to hold on to: **the FREE layer of this document's own three-layer table is, today, reachable only by editing code** — which is what the modularity law forbids." — contradicted by the measurement above (`config_from_run_manifest(m).DISCHARGE_POLICY == 'off'`)

- **D3 — the prose immediately after the check contradicts the check's own current assertion.**
  - docs/map/CON-discharge-channel.md:162-164 — "That check asserts the DEFECT and says so: it passes while a configured `off` is silently discarded in favour of the default, and goes red the day a real configuration road lands" — but the assertion at :159 now demands `== 'off'`, i.e. that the value IS restored

- **D3 — lane B2 inverted the assertion but left the prose, and the check has never once run to catch it.**
  - git show 9a7b0a625 -- docs/map/CON-discharge-channel.md is a one-line diff: "-assert config_from_run_manifest(m).DISCHARGE_POLICY == 'discharge-required.v1', 'the pop no longer discards the configured value -- F-A may be fixed; re-read this section'\n+assert config_from_run_manifest(m).DISCHARGE_POLICY == 'off', 'carriage no longer restores the configured value -- P15 may have regressed; re-read this section'"

- **D3 — what carriage did NOT deliver, per the lane that built it: the end-to-end YAML→scheduler road is still the thing E56 names as missing.**
  - docs/ERRATA.md E56 — "The end-to-end check — a YAML naming a policy, through the real `start_manifest_run`, reaching a scheduler that resolves it — is the one the modularity law actually asks for, and it is still missing." and "the defect stays OPEN at `experiments/2026-08-26-pc2-rematch/PARKED.md` F-A"

- **D3 — PARKED P5 forecast exactly this outcome and told the implementer to record it.**
  - experiments/2026-08-29-fix-docs-verify-multiline-checks/PARKED.md:211-219 — "WHY IT MATTERS BEYOND THE CHECK: that claim is the evidence for the document's own statement that this signal's FREE layer \"is, today, reachable only by editing code\" … If the claim turns out FALSE once the check can run, the document's conclusion moves with it. SCOPE: docs/map/CON-discharge-channel.md only. Bind the toolchain the policy names, re-run, and record what the assertions then say — including if they pass, which would be the more interesting outcome."

- **D4 — the check's current text, verbatim, at its current location.**
  - docs/map/INV-signal-contract.md:243-250 — "`check: python -c \"\nimport inspect\nfrom deepreason.scheduler.scheduler import Scheduler\nsrc = inspect.getsource(Scheduler)\nassert 'wander.decide(' in src and 'wander.reading_from(' in src\nfor fn in ('wander_cap_v1', 'open_lineage_v1', 'LINEAGE_POLICIES'):\n    assert fn not in src, fn\n\"`"

- **D4 — the claim it defends.**
  - docs/map/INV-signal-contract.md:238-241 — "**The consumer reads the interface and nothing else.** `scheduler.py` calls `wander.decide` and `wander.reading_from`; it never names a policy function. A scheduler that knew it was running `wander_cap_v1` would have to be edited to run anything else, which is the coupling the registry exists to prevent."

- **D4 — the comment that defeats it, verbatim, at its current line.**
  - src/deepreason/scheduler/scheduler.py:1132-1134 — "        # untouched. The policy is selected by id from `wander.LINEAGE_POLICIES`\n        # and consumed ONLY through `wander.decide` -- the scheduler is never\n        # taught which throttle it is running."

- **D4 — the comment is the ONLY occurrence: strip comments and the current check passes; the claim genuinely holds.**
  - measured over `inspect.getsource(Scheduler)`: occurrences of LINEAGE_POLICIES in raw class source = 1; occurrences outside comments = 0; current-form check on comment-stripped source = True

- **D4 — the repaired form (ast.unparse over the dedented class source) is GREEN today.**
  - measured: `ast.unparse(ast.parse(textwrap.dedent(inspect.getsource(Scheduler))))` then the same assertions → "REPAIRED CHECK PASSES"; `wander.decide(` and `wander.reading_from(` both survive unparse (the real calls are at src/deepreason/scheduler/scheduler.py:1135, :2075 and :1222)

- **D4 — the repaired form is mutation-proven RED on a real regression.**
  - measured in memory: replacing `decision = wander.decide(self.config, self._wander_reading())` with `decision = wander.LINEAGE_POLICIES['wander_cap.v1'](...)` makes the unparsed source contain LINEAGE_POLICIES → "repaired form RED on a real regression: True"

- **D4 — the registry symbols the check names are real, so the mutation is a realistic regression.**
  - src/deepreason/wander.py:142-144 — "LINEAGE_POLICIES = {\n    \"wander-cap.v1\": wander_cap_v1,\n    \"open-lineage.v1\": open_lineage_v1," with `def wander_cap_v1` at :96 and `def open_lineage_v1` at :122

- **D4 — INV-signal-contract.md itself carries a now-stale note about the parser that this tranche's predecessor fixed.**
  - docs/map/INV-signal-contract.md:214-217 — "Single-line, and that is load-bearing rather than a style choice: `docs_verify` parses a `check:` LINE BY LINE (`tools/docs_verify.py:47,75`), so a check spanning several lines is silently never run. Several already in this map do. Parked: `experiments/2026-08-28-fix-capability-cycle-share/PARKED.md` §Q1." — false since the multi-line grammar landed (tools/docs_verify.py:92-115)

- **AUTHORITATIVE FULL RUN, today, on this branch: 70 documents, 1248 checks, 9 failed.**
  - `python tools/docs_verify.py` (full, no cache) → "docs_verify [full]: 70 documents, 1248 checks, 4 workers" … "docs_verify: 9 failed", exit 1

- **The nine failing check ids, exactly as reported.**
  - same run: SEAM-llm-x-rules.md:54 (unparseable check); CON-discharge-channel.md:150 (V6_SIMULATION_TOOLCHAIN_REQUIRED); CON-run-identity.md:211; CON-run-identity.md:213; CON-run-identity.md:215; INV-frozen-surfaces.md:181; INV-frozen-surfaces.md:734; INV-signal-contract.md:243; SEAM-llm-x-verification.md:19

- **That is delta ZERO against the shallow-clone baseline: 6 full-clone rows + 3 shallow-only rows = 9.**
  - docs/AUDIT_BASELINES.md:36-47 lists exactly these six documents plus the three CON-run-identity git-history checks; the observed set matches row for row, with only the three line numbers having drifted (657→734, 222→243, 200/202/204→211/213/215)

- **The instrument's own counts have also drifted from the baseline: 69→70 documents, 1212→1248 checks.**
  - docs/AUDIT_BASELINES.md:25-26 says "**1212 checks over 69 documents**"; today's run reports "70 documents, 1248 checks"

- **--audit today reports exactly one finding, and it is the out-of-scope malformed check.**
  - `python tools/docs_verify.py --audit` → "SEAM-llm-x-rules.md:54: unparseable check: …" then "docs_verify --audit: 1 finding(s)". No vacuous check is flagged anywhere in the map.

- **--self-test and --links are green.**
  - `python tools/docs_verify.py --self-test` → "docs_verify --self-test: ok", exit 0; `python tools/docs_verify.py --links` → "docs_verify --links: 0 dangling reference(s), 70 document(s)"

- **SEAM-llm-x-verification.md has no Sweep: header today, so editing it triggers SCHEMA.md's ratchet.**
  - `python tools/docs_verify.py --coverage` → "SEAM-llm-x-verification.md: no Sweep: header (add when next touched)" … "docs_verify --coverage: 7 seam(s) swept, 19 without a Sweep: header, 2 finding(s)"

- **There are 74 multi-line checks map-wide, against SCHEMA.md's floor of 70 — four of headroom.**
  - measured via `docs_verify.documents()`: "multi-line checks: 74  (SCHEMA.md:119 asserts >= 70) / total checks: 1248 docs: 70"; the four lane-D targets are multi-line at SEAM-llm-x-verification.md:19, INV-frozen-surfaces.md:734, CON-discharge-channel.md:150, INV-signal-contract.md:243

- **The frozen-surface branch tripwire currently PASSES on this branch and must be kept passing by Lane D.**
  - docs/map/INV-frozen-surfaces.md:297 — "`check: ! git diff --name-only origin/main...HEAD | grep -qE \"capabilities/state\\.py|/harness\\.py|/invariants\\.py|/run_manifest\\.py|/qualification\\.py|llm/firewall\\.py\"`" — measured exit 0 (no src changes on this branch yet)

- **Batch-2 SETUP.md places Lane D first in integration order and is offline by construction.**
  - experiments/2026-08-29-ultracode-batch-2/SETUP.md:58 — "| D | (docs/map + measurement) | Four rotted map checks |" and :61-62 "Integration order is cheapest-first — D, E, C, B, A — with a ring after each, then ONE full gate and ONE `docs_verify` at fan-in." and :34-35 "No `OLLAMA_API_KEY` and no `env` file anywhere: this batch is OFFLINE by construction, and no lane may claim live evidence."

- **Batch-2 SETUP.md binds Lane D to push at every phase boundary, including at the moment a STOP is parked.**
  - experiments/2026-08-29-ultracode-batch-2/SETUP.md:43-49 — "> **A STOP is a phase boundary.** Work parked for an operator decision is finished work awaiting a verdict, and it must be pushed at the moment it is parked, not at the moment the verdict arrives.\n\nAccordingly: this session pushes the session branch and every lane's work at every phase boundary, and a parked STOP is pushed with its brief in the same act that parks it."


## Files

- `/home/user/DeepReason/docs/map/SEAM-llm-x-verification.md` (read-write) — D1. Read in full (168 lines). Correct the core claim at :12-17, replace the check at :19-32 with a set-pinning AST check covering BOTH sides of the seam (not just invariants.py and llm/adapter.py), rewrite — never delete — the Traps entry at :163-167, and settle the Sweep: header question SCHEMA.md's ratchet raises. Verified-at is 814268b46.
- `/home/user/DeepReason/docs/map/INV-frozen-surfaces.md` (read-write) — D2. Read in full (894 lines). Re-pin the stale digest in the check at :734-742 (assertion at :739) from b9038b84 to 02ee7e09, add a Traps/history sentence near :714-719 recording the 2026-08-28 move under commit e9457f8ff, and decide whether the duplicate digest assertion (already at :615) is kept or dropped in favour of the DISCHARGE_POLICY-leak half. Verified-at is a40450f1c. Also carries the :297 branch tripwire Lane D must keep green.
- `/home/user/DeepReason/docs/map/CON-discharge-channel.md` (read-write) — D3. Read in full (340 lines). Swap engaged_local_simulation_toolchain -> engaged_simulation_toolchain in the check at :150-160 (import line :154 and call site :157), and repair the prose at :133-148 and :162-166 that the repaired check now contradicts. Verified-at is a5a435e3e.
- `/home/user/DeepReason/docs/map/INV-signal-contract.md` (read-write) — D4. Read in full (374 lines). Rewrite the check at :243-250 to run over ast.unparse output rather than raw getsource text; while in the file, the stale parser note at :214-217 ('docs_verify parses a check: LINE BY LINE ... a check spanning several lines is silently never run') is false since the multi-line grammar landed. Verified-at is 6c65f95e8.
- `/home/user/DeepReason/docs/map/SUB-verification.md` (read-write) — D1 companion. Line 19's seam row labels llm x verification 'deliberately absent'; only the llm-side half of its stated evidence survives. Same commit as the seam per SCHEMA.md's 'map moves with the change' rule. Its Owns: header (src/deepreason/invariants.py, src/deepreason/verification/, src/deepreason/signals_read.py) is what defines the verification side of the crossing set.
- `/home/user/DeepReason/docs/map/INDEX.md` (read-write) — D1 companion. Lines 150-159 repeat the false 'the two sides import NOTHING from each other in either direction' claim as unchecked prose, and line 131 lists the pair with a dash for import count. INDEX.md carries only one check (:173, --links).
- `/home/user/DeepReason/docs/AUDIT_BASELINES.md` (read-write) — The expected-failure table at :34-47 names four of Lane D's targets by document:line; three of its line numbers are already stale and its counts (1212 checks / 69 documents) are stale against today's 1248 / 70. Its own rule at :3-8 says it moves in a non-audit tranche, in the same commit as whatever moved the value — which is this lane. NOTE: this is docs/, not docs/map/; confirm it is in scope before editing.
- `/home/user/DeepReason/docs/map/SCHEMA.md` (read-write) — The authoring contract; read in full (359 lines) before touching any map document. Also carries a claim falsified by the code: :193-194 says '--audit flags checks that pass against a deliberately mutated tree', which cmd_audit never does. Correcting it is optional for Lane D and is flagged under stops. Its self-test check at :119-124 pins multi-line checks >= 70 (today: 74).
- `/home/user/DeepReason/tools/docs_verify.py` (read) — Read in full (566 lines) to state parsing (_CHECK :59, _CHECK_OPEN :67, _read_block :92-115, parse_text :118-134), execution (run :194-209, CHECK_TIMEOUT_S :185, cache bypass :218), and --audit's vacuous detection (_VACUOUS :78-80, cmd_audit :438-453, self-test pins :504 and :506-524). READ ONLY unless a decision is taken to extend --audit, which would be a code change outside this lane's 'no src' framing and needs its own nod.
- `/home/user/DeepReason/src/deepreason/invariants.py` (read) — FROZEN SURFACE 3. Read only, to enumerate the crossings for D1: :21 (module-level route_fingerprint), :1214, :1215-1218, :1260-1262, :4101. Also the consumers at :1335, :2546, :3870, :4103 that justify each import. NEVER EDIT.
- `/home/user/DeepReason/src/deepreason/verification/report.py` (read) — FROZEN SURFACE 3 (verification/). Read only. Holds the sixth crossing FINDINGS.md missed: :721 'from deepreason.llm.firewall import route_fingerprint' inside _transaction_findings (:711), consumed at :767. NEVER EDIT.
- `/home/user/DeepReason/src/deepreason/llm/firewall.py` (read) — FROZEN-ADJACENT. Read only. Defines route_fingerprint at :115 — the symbol at the centre of D1. NEVER EDIT.
- `/home/user/DeepReason/src/deepreason/llm/adapter.py` (read) — Read only. The llm-side half of the seam check's subject; its only textual mention of verification is a comment at :947. Used to demonstrate that the reverse direction is genuinely zero.
- `/home/user/DeepReason/src/deepreason/scheduler/scheduler.py` (read) — D4. Read only. The defeating comment is at :1132-1134; the real interface calls are at :1135, :1222, :2075. Lane D changes the CHECK, not this file — and this file is another lane's cone.
- `/home/user/DeepReason/src/deepreason/wander.py` (read) — D4. Read only. LINEAGE_POLICIES at :142-144, wander_cap_v1 at :96, open_lineage_v1 at :122 — the names the repaired check must still forbid, and the registry that makes the mutation proof realistic.
- `/home/user/DeepReason/src/deepreason/run_manifest.py` (read) — FROZEN SURFACE 4. Read only. The validator that rejects D3's fixture is at :3595-3614, raising V6_SIMULATION_TOOLCHAIN_REQUIRED at :3605; compile_run_manifest constructs the model at :4023. NEVER EDIT.
- `/home/user/DeepReason/src/deepreason/v6_policy.py` (read) — D3. Read only. engaged_inquiry_capability_policy at :611, engaged_local_simulation_toolchain at :635, engaged_contained_simulation_toolchain at :658, and the fix's target engaged_simulation_toolchain at :680.
- `/home/user/DeepReason/src/deepreason/qualification.py` (read) — FROZEN SURFACE 5. Read only. qualification_subject_digest / qualification_subject_payload are what D2's pin measures. NEVER EDIT — Lane D corrects an assertion in a document, not the surface.
- `/home/user/DeepReason/tests/test_reusable_qualification.py` (read) — D2. Read only. Supplies _manifest and _profile, the fixture every qualification-digest pin in INV-frozen-surfaces.md is measured against.
- `/home/user/DeepReason/tests/test_discharge_wire.py` (read) — D2 evidence. Read only. Its docstring at :194-217 records the b9038b84 -> 02ee7e09 move, dated 2026-08-28, with the reason — the committed test pin that WAS updated while the map pin was not.
- `/home/user/DeepReason/tests/test_allocation_signal_consumption.py` (read) — D2 evidence. Read only. The second digest pin moved by the same commit (f3bb6562 -> 83454b08), and the target of INV-frozen-surfaces.md:420's pytest node test_the_shipped_qualification_subject_digest_does_not_move.
- `/home/user/DeepReason/experiments/2026-08-29-fix-docs-verify-multiline-checks/FINDINGS.md` (read) — The lane's authority. 184 lines, read in full. Class (b) is B1-B4 at :32-115; the full-clone addendum is at :167-184.
- `/home/user/DeepReason/experiments/2026-08-29-fix-docs-verify-multiline-checks/PARKED.md` (read) — The five ready-to-send prompts. 220 lines. P1 (=D1) at :13-62, P2 (=D2) at :66-100 including its escalation clause, P4 (=D4) at :143-177, P5 (=D3) at :181-220. P3 (SEAM-llm-x-rules.md:54) is NOT in Lane D's four.
- `/home/user/DeepReason/experiments/2026-08-27-change-execution-safety/REQUEST.md` (read) — D2's grant. The operator's verbatim words at :155-157 and constraint C7 at :165-175. Cite this in the re-pin's Traps entry.
- `/home/user/DeepReason/experiments/2026-08-27-change-execution-safety/DELIVERY.md` (read) — D2's priced cost, :386-393 — the two pins that moved, and the ~14-minute requalification the move bought.
- `/home/user/DeepReason/experiments/2026-08-29-ultracode-batch-1/BATCH.md` (read) — The prior batch's fan-in disposition. :462-500 gives the 10-failure table with the same line numbers Lane D will see, and its measurement that the :734 pin was already wrong before that branch existed.
- `/home/user/DeepReason/experiments/2026-08-29-ultracode-batch-2/SETUP.md` (read) — Batch-2's anchor, environment, integration order and the push-at-every-boundary rule. 62 lines, read in full.
- `/home/user/DeepReason/docs/ERRATA.md` (read) — D3 context. E56 (the discharge entry, from line 1545) states the still-missing end-to-end YAML->start_manifest_run->scheduler check and points at the still-OPEN park experiments/2026-08-26-pc2-rematch/PARKED.md F-A. Read before rewriting CON-discharge-channel's conclusion. Note ERRATA carries TWO entries numbered E56.
- `/home/user/DeepReason/experiments/2026-08-29-ultracode-batch-2/` (new) — Lane D's own tranche artifacts (the lane's RESULTS/evidence, and the docs_verify before/after captures) belong under this batch directory. Scratch files go in the session scratchpad, never the repo.

## Work items

### D0 — Record the pre-work baseline: paste today's authoritative full run (70 documents, 1248 checks, 9 failed) and the nine check ids into the lane's evidence, and note the three line numbers that have drifted from docs/AUDIT_BASELINES.md (657->734, 222->243, 200/202/204->211/213/215) plus the count drift (1212/69 -> 1248/70). Do NOT re-run it concurrently with a pytest gate.

  DONE-CRITERION: `python tools/docs_verify.py` output committed under experiments/2026-08-29-ultracode-batch-2/ showing `docs_verify: 9 failed` with the nine ids; `git rev-parse --is-shallow-repository` = true recorded beside it.

### D1-a — Correct SEAM-llm-x-verification.md's core claim (:12-17). Replace 'no import in either direction' with the measured relationship: ONE-DIRECTIONAL. verification -> llm exists at seven (file, module, symbol) crossings across six import statements — invariants.py:21 (module-level, route_fingerprint from llm.firewall), invariants.py:1214 (ConjecturerOutput), :1215-1218 (AliasTable, wire_contract_for), :1260-1262 (ReferenceFreeConjecturerWireContract), :4101 (HashingEmbedder), and verification/report.py:721 (route_fingerprint) — while llm -> verification/invariants/signals_read is ZERO in every form. Say WHY each crossing exists (route-digest re-derivation, wire-contract authority set, detection totality) and keep the document's real point: the substantive agreement is still what LLMAttempt's fields MEAN. Do not write line numbers into prose (SCHEMA.md:358).

  DONE-CRITERION: `grep -c 'no import in either direction' docs/map/SEAM-llm-x-verification.md` returns 0, and the document names both `route_fingerprint` and `verification/report.py` as crossings.

### D1-b — Replace the check at SEAM-llm-x-verification.md:19-32 with one that pins the crossing SET rather than asserting absence, and that covers the whole of both sides (all of src/deepreason/llm/ and invariants.py + src/deepreason/verification/), not just adapter.py. A verified candidate exists and passes today: AST-collect every ImportFrom/Import naming `deepreason.llm*` from the verification side into (path, module, symbol) triples and assert equality with the frozen 7-element set; assert the reverse set (llm/ naming deepreason.invariants|deepreason.verification) is empty. Multi-line form, column 0, closing backtick on its own line.

  DONE-CRITERION: The check runs green under `python tools/docs_verify.py`; and a mutation proof (in a scratch copy, per SCHEMA.md's 'do not measure the tree while a falsification pass is running') shows it goes RED both when an eighth `deepreason.llm.*` import is added to invariants.py AND when any `deepreason.invariants` import is added under src/deepreason/llm/.

### D1-c — Rewrite (never delete) the Traps entry at SEAM-llm-x-verification.md:163-167. Its lesson — 'zero import traffic is not zero coupling' — survives as a generalisation but its premise about THIS pair is false; restate it as 'the measured traffic is one-directional and was invisible to the matrix anyway, because the matrix counts package-to-package imports and five of the six crossings are function-local'. Add, per CLAUDE.md, that the trap was found by the first execution of the seam's own check on 2026-08-29.

  DONE-CRITERION: The Traps section still contains the original lesson's title, now carrying the corrected premise and a date; `git diff` shows no deleted Traps bullet.

### D1-d — Move the two sibling documents in the SAME commit: SUB-verification.md:19's 'deliberately absent' seam row, and INDEX.md:150-159's paragraph claiming 'the two sides import NOTHING from each other in either direction'. Keep INDEX.md's real point (a pair absent from the coupling matrix can still be load-bearing) and correct only the factual premise; note that function-local imports are exactly what the matrix cannot see, which INDEX.md already says at :136-137 about other pairs.

  DONE-CRITERION: `grep -rn 'import NOTHING from each other' docs/map/` returns nothing, and SUB-verification.md's llm row no longer asserts the pair is import-free in both directions.

### D1-e — Settle SCHEMA.md's Sweep: ratchet for SEAM-llm-x-verification.md, which --coverage today reports as 'no Sweep: header (add when next touched)'. Either add a header whose left side is the field the agreement moves (candidate: `attempt_trace|split_legs` && the verification-side symbols) or, per SCHEMA.md:186-189, deliberately leave it off and say in the body why every candidate spec would flag readers rather than enforcement sites.

  DONE-CRITERION: `python tools/docs_verify.py --coverage` either stops listing SEAM-llm-x-verification.md, or the document body contains a sentence naming the ratchet and why the header is withheld; the --coverage finding count does not increase.

### D2-a — Re-pin the stale digest. In INV-frozen-surfaces.md's check at :734-742, change the asserted value at :739 from b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386 to 02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713, keeping the DISCHARGE_POLICY-leak assertion. If the duplication with the already-green pin at :610-622 is judged redundant, drop the digest assertion here and keep only the leak assertion — but do not drop both.

  DONE-CRITERION: `python tools/docs_verify.py` no longer lists INV-frozen-surfaces.md:734 (or its successor line); the check exits 0 when run standalone.

### D2-b — Write the history the re-pin owes. PARKED P2 required that if the digest actually MOVED, that is 'a different and larger finding'. It did: commit e9457f8ff (2026-08-28), tranche experiments/2026-08-27-change-execution-safety/, under the operator's conditional grant 'Frozen surface changes are permitted as long as you document what is affected'; the default simulation runner became the contained one, so the compiled policy binds python@deepreason-public-contained.v1 and the subject moved. Two committed TEST pins were updated in that commit (tests/test_discharge_wire.py, tests/test_allocation_signal_consumption.py); this map pin was DARK and was not. Correct the prose at :714-719 which still asserts the digest is 'unchanged at b9038b84…' as a present fact, and add a Traps entry naming the finding and its instrument.

  DONE-CRITERION: INV-frozen-surfaces.md cites e9457f8ff and experiments/2026-08-27-change-execution-safety/, the prose near the F1 contact no longer states b9038b84 as the current value, and a Traps entry names the 2026-08-29 first-execution as how it was found.

### D2-c — Prove no OTHER pin moved — the lane brief's stop condition. Run every check in INV-frozen-surfaces.md individually and record the verdicts. Already measured green today: :297, :347, :525, :610, :623, :659, :673, :721, :727. Already measured red and NOT this lane's: :181 (the falsified transport_failure census, a pre-existing baseline row). Note that :420 also carries a digest-adjacent pytest node (test_the_shipped_qualification_subject_digest_does_not_move) and passes in the full run.

  DONE-CRITERION: A committed table of per-check verdicts for INV-frozen-surfaces.md showing exactly two reds (:181 pre-existing, :734 this lane's) before the fix and exactly one (:181) after.

### D3-a — Repair the fixture at CON-discharge-channel.md:150-160: change the import at :154 and the call at :157 from `engaged_local_simulation_toolchain` to `engaged_simulation_toolchain`, which returns whichever toolchain the engaged policy names. Verified today: with that swap the manifest compiles and both assertions pass ('DISCHARGE_POLICY' absent from engine_config_json; config_from_run_manifest restores 'off'; compile_notices carries one ENGINE_CONFIG_FIELD_NOT_CARRIED at /engine_config/DISCHARGE_POLICY).

  DONE-CRITERION: `python tools/docs_verify.py` no longer lists CON-discharge-channel.md:150; and the check's second assertion still names P15 in its message so a carriage regression is legible.

### D3-b — Repair the prose the now-runnable check contradicts. Lines 133-148 ('The default is the ONLY road, and that is a defect'; 'the field falls back to its CODE DEFAULT and a YAML line naming a preset is inert'; 'the FREE layer ... is, today, reachable only by editing code') and 162-166 ('That check asserts the DEFECT') are false since lane B2's carriage fix (commit 9a7b0a625). Restate what is now MEASURED — a configured DISCHARGE_POLICY survives the compile/echo/rebuild round trip through config_from_run_manifest — and state plainly what is still NOT proven: the end-to-end path from a YAML file through start_manifest_run to a scheduler that resolves the preset, which docs/ERRATA.md E56 names as still missing. Do NOT declare experiments/2026-08-26-pc2-rematch/PARKED.md F-A closed.

  DONE-CRITERION: `grep -n 'reachable only by editing code' docs/map/CON-discharge-channel.md` returns nothing; the section states the measured round-trip result and names the still-unproven end-to-end road with its ERRATA reference; the F-A park is still described as open.

### D4-a — Repair the check at INV-signal-contract.md:243-250 so it binds CODE, not source TEXT. Verified form: `ast.unparse(ast.parse(textwrap.dedent(inspect.getsource(Scheduler))))` then the same two assertions. Comments and formatting vanish under unparse; the real calls survive (`wander.decide(`, `wander.reading_from(`). Do not touch src/deepreason/scheduler/scheduler.py — it is another lane's cone and the claim it carries is TRUE.

  DONE-CRITERION: `python tools/docs_verify.py` no longer lists INV-signal-contract.md:243; the standalone command exits 0.

### D4-b — Mutation-prove the repaired D4 check both ways, in a scratch copy, and commit the output. RED: plant a real `wander.LINEAGE_POLICIES[...]` call in the Scheduler body and show the check fails. GREEN: with the explanatory comment present and unmodified, the check passes. Both were verified in memory during reconnaissance and reproduce.

  DONE-CRITERION: A committed proof file under experiments/2026-08-29-ultracode-batch-2/ showing the RED transcript and the GREEN transcript, with `git status` clean afterward and `__pycache__` cleared before the GREEN measurement (SCHEMA.md:181-184).

### D4-c — While in INV-signal-contract.md, correct the stale note at :214-217 which tells readers 'docs_verify parses a `check:` LINE BY LINE (tools/docs_verify.py:47,75), so a check spanning several lines is silently never run'. That was true before 2026-08-29 and is false now (tools/docs_verify.py:92-115 reads multi-line blocks; an unreadable opener is a loud failure). Rewrite it to record the history rather than deleting it, and drop the now-obsolete parked pointer or mark it closed.

  DONE-CRITERION: The document no longer instructs authors that multi-line checks are silently skipped; `grep -n 'silently never run' docs/map/INV-signal-contract.md` returns nothing.

### D5 — Update docs/AUDIT_BASELINES.md's docs_verify entry in the same commit as the fixes (its own rule at :3-8). Remove the four rows this lane repairs, keep SEAM-llm-x-rules.md:54 (P3, out of scope) and INV-frozen-surfaces.md:181, refresh the check/document counts (1212/69 -> the post-fix measured values), and refresh the three stale line numbers in whatever rows survive. State the new expected totals for both a full and a shallow clone.

  DONE-CRITERION: The post-fix `python tools/docs_verify.py` failure set matches docs/AUDIT_BASELINES.md's table row for row on this shallow container (expected: 2 non-shallow rows + 3 shallow rows = 5 failed), with the transcript committed beside it.

### D6 — Close with ONE authoritative full run: `python tools/docs_verify.py` (full mode, never --fast, never concurrently with a pytest gate — SUB-application.md:403 already uses 54% of the 300 s check timeout on an idle box, parked as P16/P19). Also re-run --self-test, --links and --audit. Advance Verified-at ONLY on documents whose full check sets were actually re-derived (SCHEMA.md:269-272).

  DONE-CRITERION: Committed transcripts for all four modes; `--self-test` ok; `--links` 0 dangling; `--audit` still exactly 1 finding (SEAM-llm-x-rules.md:54); and a Verified-at audit showing each advanced stamp corresponds to a document whose checks were run.


## Risks

- LINE NUMBERS IN EVERY UPSTREAM ARTIFACT ARE STALE. FINDINGS.md and PARKED.md cite :657, :222, :533 and scheduler.py:1127; docs/AUDIT_BASELINES.md cites :657, :222, :200/:202/:204. Today the same checks are at INV-frozen-surfaces.md:734, INV-signal-contract.md:243, INV-frozen-surfaces.md:610, scheduler.py:1132 and CON-run-identity.md:211/:213/:215. Re-locate by anchor text, never by the cited number, and expect them to shift again as this lane's own edits land — every edit above or inside a document moves its later check line numbers, and the failure report keys on them.
- SCHEMA.md's self-test check pins multi-line checks at >= 70; the tree has 74. All four Lane D targets are multi-line. Collapsing more than four of them to single-line form turns SCHEMA.md's own check RED — a self-inflicted failure that looks like an unrelated regression.
- The frozen-surface branch tripwire at INV-frozen-surfaces.md:297 greps `git diff --name-only origin/main...HEAD` for the seven frozen paths and cannot tell a granted contact from an ungranted one. It PASSES today on this branch. Lane D must not touch any of capabilities/state.py, harness.py, invariants.py, run_manifest.py, qualification.py, verification/ or llm/firewall.py, or it fires as a tenth failure. At batch fan-in it will likely fire anyway from lanes A/B/C — that is parked P16 and not Lane D's.
- The D3 repair CHANGES A CONCLUSION, not just a fixture. The document currently tells readers the discharge channel's FREE layer is unreachable and cites that as a modularity-law violation with an open park (F-A) and an ERRATA entry (E56). Overstating the repair — 'the road exists now' — would silently close a defect nobody verified end to end. Carriage was measured only at the compile/echo/rebuild round trip; the YAML -> start_manifest_run -> scheduler path that E56 names remains unmeasured.
- The D3 check as repaired passes for TWO reasons at once (the manifest compiles AND carriage restores the value), so a future carriage regression and a future toolchain-default change both surface as the same red line. Keep the assertion messages distinct so the failure text says which one moved; the existing 'P15 may have regressed' message does this for the second half only.
- docs_verify's --fast/--failed cache (.docs_verify_cache.json) keys on the check text plus the content of paths the command NAMES (tools/docs_verify.py:145-164). Several Lane D checks read files they do not name (inspect.getsource of a class, tests.test_reusable_qualification imports), so a --fast run can report a stale green. Only the default full mode is admissible evidence for this lane.
- Running the full docs_verify concurrently with a pytest gate risks wall-clock timeouts, not logical failures: CHECK_TIMEOUT_S is 300 s and batch-1 parked P19 recording SUB-application.md:403 at 160.88 s on an idle box. Serialize the fan-in instruments.
- This container is a SHALLOW clone, so the three CON-run-identity git-history checks fail for an environmental reason and the correct baseline is 9, not 6. Any report that quotes 6 without saying which clone shape it was measured on is unreadable. `git fetch --unshallow` is a mutating command and was deliberately not run during reconnaissance.
- docs/ERRATA.md carries TWO entries numbered E56 (one at line 1475 about SEAM-llm-x-rules's crossing count, one from line 1545 about the discharge channel). CON-discharge-channel.md:166 cites 'E56' ambiguously. If the D3 prose repair adds an ERRATA reference, disambiguate it or the citation is useless.
- The repaired D1 check pins an exact 7-element set. That is stronger than the current check but it is also brittle by design: any legitimate future import from verification into llm will fail it. That is the point (SCHEMA.md rule 6, 'counts are claims'), but the document must say so in prose so the next author widens the set deliberately rather than deleting the check.
- SUB-llm.md:27's grep — the only other thing policing this boundary — omits `invariants` from its forbidden-package list, so an llm -> invariants import would pass it. Lane D should note the gap in the seam document even though widening SUB-llm.md:27 is arguably a separate change.
- Batch-2 SETUP.md binds this session to push at every phase boundary, including the moment a STOP is parked. A Lane D STOP brief written and not pushed is exactly the loss batch 1 paid for (experiments/2026-08-29-ultracode-batch-1/LOSS.md).

## Stops (bubble, never resolve in-batch)

- D1 ROAD (ii) IS A HARD STOP. PARKED P1 prices two roads: narrow the document, or treat the import as a real violation and remove it. Road (ii) edits src/deepreason/invariants.py (frozen surface 3) and reaches src/deepreason/llm/firewall.py (frozen-ADJACENT). NO GRANT EXISTS on this branch. The lane brief pre-selects road (i) ('The code is FROZEN and stays untouched — we correct the DOCUMENT'), so this stop should not fire; if the implementer concludes the import must go, STOP and bubble rather than editing, per INV-frozen-surfaces.md's grant procedure.
- D2 REQUIRES A DISCLOSURE THAT PARKED P2 CLASSIFIED AS AN ESCALATION. P2's prompt says: 'If the history shows the digest DID move at some point and :533 was updated while :657 was not, say so — that is a different and larger finding, and it goes to the operator before any edit.' That is exactly what the record shows: the digest moved on 2026-08-28 in commit e9457f8ff under the operator's conditional grant, the two committed test pins were updated, and the dark map pin was not. The lane brief grants THIS ONE RE-PIN, which supersedes P2's escalation for the edit itself — but the finding must be written into the tranche record and surfaced to the operator in the same act, not folded silently into a one-character diff.
- ANY OTHER PIN MOVING IS A STOP — and none does. Every other check in INV-frozen-surfaces.md was run individually and measures as asserted (:297, :347, :525, :610, :623, :659, :673, :721, :727 all exit 0), and the authoritative full run confirms it. The one other red in that file, :181 (the falsified 'zero committed transport_failure attempts' census), is a PRE-EXISTING baseline row belonging to the 2026-08-25 frozen-surface grant, not to Lane D — do not repair it here.
- D3's SECOND HALF IS A CLAIM REVERSAL, NOT A FIXTURE FIX, AND NEEDS A NOD BEFORE IT LANDS. Repairing the check makes the document's own conclusion ('the FREE layer is, today, reachable only by editing code') false. Rewriting that conclusion touches a claim that an ERRATA entry, an open park (experiments/2026-08-26-pc2-rematch/PARKED.md F-A) and a modularity-law citation all rest on. Recommended disposition: correct the prose to exactly what is measured (the round trip restores the configured value) and explicitly leave F-A open pending the end-to-end YAML->start_manifest_run->scheduler check E56 names as still missing. If the implementer wants to close F-A, that is a bubble.
- docs/AUDIT_BASELINES.md IS OUTSIDE 'docs/map + measurement' AS THE BRIEF WORDS IT, BUT ITS OWN RULE REQUIRES IT TO MOVE HERE. It says the file 'moves only in a non-audit tranche, in the same commit as whatever moved the value'. Fixing four of its six expected-failure rows without updating it leaves the next audit reading a delta of -4 as a finding. Confirm this file is in Lane D's write set before editing; if it is not, the lane must park a one-line prompt for whoever owns it and say so at fan-in.
- SCHEMA.md CARRIES A CLAIM ITS OWN TOOL FALSIFIES, and correcting it edits the contract every map document is written against. SCHEMA.md:193-194 says '`tools/docs_verify.py --audit` flags checks that pass against a deliberately mutated tree'; cmd_audit (tools/docs_verify.py:438-453) never mutates and never executes — it applies a static `_VACUOUS` regex (:78-80) to the command's leading token. This is a genuine docs-vs-code drift and it is in docs/map, but it is a fifth finding beyond the lane's four. Recommend: report it, and either correct the sentence in this lane with an explicit nod or park it as a one-line prompt.
- EXTENDING --audit TO CATCH D4's SHAPE IS A CODE CHANGE AND IS OUT OF THIS LANE'S 'NO src/ CHANGES' FRAMING — but the answer to the brief's question is YES, partially, and here is exactly where. The detection lives at tools/docs_verify.py:78-80 (`_VACUOUS`) and is applied at :448-451 inside cmd_audit's per-check loop; it is pinned by cmd_self_test at :504 and by the fixture-based audit assertions at :506-524, which is the only gate this file has (:459-461: 'nothing in tests/ exercises it'). `_VACUOUS` itself CANNOT be stretched to cover D4: it is anchored at the command's first token and detects checks that CANNOT FAIL, whereas D4 is the opposite defect — a check that fails on a TRUE claim. A separate, additive lint in the same loop could catch the SHAPE: flag any check that derives a string from raw source text (`inspect.getsource`, `.read_text()`, or an unanchored `grep -q <bare-identifier> <*.py>`) and then makes an identifier-membership assertion against it, because comments and docstrings are inside that string. It must be ADVISORY, not a new failure: SCHEMA.md:85 itself ships such a check (`! grep -q "deepreason.scratch" src/deepreason/rules/crit.py`) as a worked example, and SUB-llm.md:27's anchored `^[[:space:]]*(from|import)` form is comment-immune, so a hard rule would flag legitimate checks. Any such addition also needs a matching arm in cmd_self_test.
