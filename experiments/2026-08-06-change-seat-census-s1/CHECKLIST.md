# Checklist for: seat census — Rung S1 of role-seat separation
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

- [x] 1. (S1) Run the full-tree call-site sweep and paste raw output
      into a new `experiments/2026-08-06-change-seat-census-s1/CENSUS.md`
      under a "Raw sweep" section: `grep -rn "\.call(" src/deepreason
      --include="*.py"` and `grep -n
      "render_role_prompt\|EndpointLease(\|select_lease" src/deepreason/cli/doctor.py`.
      done-when: CENSUS.md exists with a "## M0 — raw sweep" section
      containing both pasted command blocks verbatim.
      DONE: CENSUS.md created with "## M0 — raw sweep" containing both
      commands' full pasted output (43 lines from the `.call(` sweep,
      4 lines from the doctor.py sweep).

- [x] 2. (S1) Triage every hit from the raw sweep: mark each as an
      LLMAdapter-family call site (promoted) or excluded (`.call(` on a
      non-adapter object, e.g. a pydantic method), one line per hit with
      the reason for exclusions.
      done-when: CENSUS.md has an "## Excluded hits" subsection whose
      entries plus the promoted-site count together equal the total
      line count of the raw sweep (paste the arithmetic: total lines =
      excluded + promoted).
      DONE: 0 excluded, 44 promoted (43 `adapter.call`-family +
      1 `doctor.py` `render_role_prompt` dispatch), 3 non-dispatch
      evidence lines (2 `EndpointLease(` construction, 1 import) folded
      into the doctor.py row's evidence, not double-counted as sites.
      Arithmetic pasted in CENSUS.md's "Excluded hits" section.

- [x] 3. (S3) Paste `select_lease`, `EndpointLease`,
      `leases_from_endpoints`, `leases_from_manifest` source from
      `src/deepreason/llm/firewall.py` and state, in one paragraph
      grounded only in that pasted text, what `select_lease` can vary
      (role, seat index) and what it cannot (anything not keyed by
      `(role, seat)`).
      done-when: CENSUS.md has a "## select_lease degrees of freedom"
      section with the pasted source and the derived-variance paragraph.
      DONE: section added with `Route`/`EndpointLease`/
      `leases_from_endpoints`/`leases_from_manifest`/`select_lease`
      source (line ranges verified against fresh `sed -n` output) and
      the derived-variance paragraph.

- [x] 4. (S2) Build the M-numbered table: one row per promoted call site
      from step 2, columns = M#, file:line, role rendered,
      template_role (if any), lease selection path (`select_lease` via
      `_render_request` vs. doctor.py's direct `EndpointLease`
      construction), frozen-per-role-today (Y/N + evidence pointer to
      step 3's finding or a site-specific deviation if found).
      done-when: `grep -c "^| M" experiments/2026-08-06-change-seat-census-s1/CENSUS.md`
      equals the promoted-site count recorded in step 2.
      DONE: `grep "^| M" CENSUS.md | grep -v "^| M#" | wc -l` = 44,
      matching the 44 promoted sites. Table also cites a new,
      more-direct piece of evidence found while building it
      (`preparation.py:276`, `roles={role: dict(endpoint) for role in
      V3_CANONICAL_ROLES}`) for the frozen-per-role column, plus the
      genuine v6 per-seat PRESENTATION nuance
      (`resolve_route_seat_base_profile`) reached by M42/M44 — recorded,
      not glossed over.

- [x] 5. (S10, A1) For every plan-named module confirmed to hold zero
      call sites of its own (workloads/website.py, workloads/code.py,
      workloads/formal.py, workloads/text.py, workloads/simulation.py,
      qualification.py, capabilities/simulation.py,
      capabilities/research.py, scratch/conjecture.py,
      scratch/service.py), add a "## Delegating modules" subsection row
      with the pasted zero-hit grep and the real owning file it
      delegates to.
      done-when: CENSUS.md's "## Delegating modules" subsection has one
      row per module listed above, each backed by a pasted command
      showing zero `.call(`/`select_lease`/`render_role_prompt` hits in
      that module.
      DONE: 10/10 modules confirmed zero-hit (fresh grep loop pasted)
      with a delegation target and evidence pointer each (module
      docstrings, import lists, and constructor dependency shapes).

- [x] 6. (S1,S2,S3,S10) [COMMIT] Commit CENSUS.md.
      done-when: `git log -1 --stat` shows CENSUS.md added, pushed to
      `origin/claude/seat-census-rung-s1-7gphj9`.

- [x] 7. (S6) Author `docs/map/CON-seats.md` following
      `docs/map/SCHEMA.md`'s convention (doc-id comment, `Verified-at`/
      `Verify`/`Owns`/`Seams` headers, prose "What it is"/"Where it
      lives"/"The rules it obeys" sections, `` `check:` `` lines at
      column 0), naming the seat concept (role -> lease -> route) and
      cross-referencing `llm/roles.py`, `llm/firewall.py`,
      `llm/adapter.py`, and `cli/doctor.py`'s bypass of `select_lease`.
      done-when: `python tools/docs_verify.py --self-test` exits 0 and
      the file contains at least one `` `check:` `` line at column 0.
      DONE: `docs_verify --self-test: ok`. File has 6 `check:` lines,
      an "## Traps" section, and reuses existing `DR-SEAM-llm-x-manifest`/
      `DR-SEAM-llm-x-rules` (both already exist) rather than inventing
      new seam documents (out of scope per S8/R9).

- [x] 8. (S6, A3) Add a `docs/map/INDEX.md` row linking to
      `CON-seats.md` in the concept table.
      done-when: `grep -n "CON-seats" docs/map/INDEX.md` shows the new
      row.
      DONE: `64:| \`CON-seats.md\` | how a role becomes a provider
      request: \`select_lease\`, \`EndpointLease\`, and today's
      one-profile-per-run mint |`

- [x] 9. (S7) Run `python tools/docs_verify.py` (full mode, no
      `--fast`) and paste the complete output; fix `CON-seats.md` and
      re-run until the summary line reads 0 failed. Also run
      `python tools/docs_verify.py --links` as a non-blocking bonus
      check (A3) and paste its result too.
      done-when: the full-mode run's pasted output ends with a summary
      line containing "0 failed".
      DONE (with an environment-preflight detour, no src/ or CON-
      seats.md fix needed): first full run found `pytest`/`jsonschema`
      missing from this container (declared `dev` extra + one
      undeclared test import) -- 295 then 2 failures, both purely
      "ModuleNotFoundError", zero relation to CON-seats.md's own 6
      checks (all green on the first run already). Installed
      `pip install -e ".[dev]" --break-system-packages` and
      `pip install jsonschema --break-system-packages` (environment
      completion, not a src/ or doc change) and re-ran:
      `docs_verify [full]: 52 documents, 823 checks, 4 workers` /
      `docs_verify: 0 failed`. `--links`: `docs_verify --links: 0
      dangling reference(s), 52 document(s)`.

- [x] 10. (S6,S7) [COMMIT] Commit `docs/map/CON-seats.md` and the
      `INDEX.md` row together.
      done-when: `git log -1 --stat` shows both files, pushed.

- [x] 11. (S9) Write `PARKED.md` in the tranche dir: every defect
      noticed while reading call sites this rung (file:line,
      description, which step/grep surfaced it), formatted so
      `deepreason-orchestrator`/`dr-set-goal` can start directly from an
      entry; if none surfaced, one line saying so.
      done-when: `PARKED.md` exists in the tranche dir.
      DONE: P1 (jsonschema undeclared dev dependency, reproduce steps +
      ready-to-run fix shape) + a note that the v6 per-seat presentation
      nuance is a measured fact for S2, not a defect.

- [x] 12. (S5) Spot-check: re-run 3 pasted commands from CENSUS.md
      (chosen across steps 1, 3, and 4/5) and diff their fresh output
      against what is pasted in the file.
      done-when: all 3 diffs are empty (paste `diff` invocations and
      their empty results).
      DONE: 3/3 exact-match confirmed (M0 raw sweep, `select_lease`
      source, `preparation.py:263-277` mint-time fact) — first attempt
      used a faulty sed-extraction script that produced false
      mismatches; redone with direct `grep -F` containment against
      fresh command output, all 3 pass.

- [x] 13. (S8) Re-read CENSUS.md and CON-seats.md in full; confirm no
      sentence recommends or decides any Rung S2 question (SeatBinding
      shape, manifest/qualification-contact choice, priced options).
      done-when: `grep -inE "should bind|recommend|SeatBinding|propose
      (a|the) (design|binding)"` over both files returns nothing, or any
      hit is confirmed to be explicitly labeled "not decided here, S2
      territory."
      DONE: zero hits. Manual re-read confirms both documents describe
      only present-tense mechanism (what exists), with the one
      forward-looking sentence in CON-seats.md ("this is measured, not
      designed, territory... this document describes only what
      exists") explicitly disclaiming S2 scope.

- [x] 14. (S4) Confirm no `src/` file was touched by this tranche.
      done-when: `git diff --stat 4fa0ce6d..HEAD -- src/` produces no
      output.
      DONE, but corrected the base commit first: `4fa0ce6d` is the OLD
      designated branch tip from before this session restarted the
      branch onto `origin/claude/delivery-rungs-handover-m22sdy`
      (REQUEST.md's "Standing constraints" explains why) — diffing
      against it also shows that upstream branch's own prior `src/`
      work, not this tranche's. The correct base is `7a6d1cdb`, this
      tranche's actual starting commit (REQUEST.md's first commit
      parent). `git diff --stat 7a6d1cdb..HEAD -- src/` produces no
      output: confirmed clean.

- [x] 15. (all) [COMMIT] Final commit of any remaining tranche
      changes, push with retry, confirm clean tree.
      done-when: `git status --porcelain` is empty and
      `git rev-parse HEAD` equals
      `git rev-parse origin/claude/seat-census-rung-s1-7gphj9`.
