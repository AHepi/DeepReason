# F1 — the discharge-required criticism channel

**Tranche.** `experiments/2026-08-26-change-f1-discharge-criticism-channel/`,
REBUILD program tranche F1, routed through `dr-change-orchestrator`.
**Branch.** `claude/rebuild-discharge-criticism-channel-2b8z8i`.
**Base.** `origin/main` at `4760a32ef`.
**Authority.** The operator's words, verbatim in REQUEST.md: *"rebuild. These
are massive issues that may explain why the results are terrible."* Four
amendments, all ledgered.

Every number below is pasted from a command, and every command is committed.
`coupling.json` is emitted by `coupling.py`; the digests by `digests.py`; the
mutation records under `proof/`. If a figure here is not in one of those, it is
not this tranche's figure.

---

## 2026-08-26 — segment 1: what was built, and what it measures

W2 measured that criticism on this tree did no causal work and named the reason
in one line: **nothing that makes the next candidate was ever shown it.** Across
the two newest and largest committed roots, 0 of 196 LLM attacks reached a later
conjecture dispatch; three of four placebo-corrected coupling rates were zero or
negative; not one of 92 coupled changes improved a score
(`experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`).

F1 builds the structure the external protocol names as the one that coupled
(`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q5): criticism enters the
writer's WORKING CONTEXT, and submission requires it DISCHARGED. It
deliberately does **not** build the obvious alternative, an acknowledgment
requirement, which the same source measured as actively harmful.

**The headline, from W2's OWN committed instruments run unmodified over two
stub-driven roots that differ only in `Config.DISCHARGE_POLICY`:**

| arm | n | CouplingRate | PlaceboRate | **Coupling − Placebo** | NeglectRate |
|---|---|---|---|---|---|
| channel **on** | 6 | 1.0 | 0.0 | **+1.0** | 0.0 |
| channel **off** | 11 | 0.0 | 0.0 | **0.0** | 1.0 |

The off arm reproduces W2's own shape on this tree — total neglect, zero
placebo-corrected coupling. The on arm is the first nonzero placebo-corrected
coupling this repository has recorded.

`census.py` and `q5.py` are the HEADLINE rather than this tranche's own
reproduction of R1, and that is deliberate: a rate computed by the instrument
that produced the original finding is not open to the objection that the new
tranche scored its own homework. The reproduction is kept as a cross-check and
must agree, which `coupling.json` asserts rather than leaving to the eye.

### The three mechanisms

**C1 — criticism renders inside the writer's binding block.** Open criticisms on
a problem render at pack priority 2, WITH `criteria` — the block stating what a
candidate is bound by — above `mandatory-interface` and far above every advisory
section. `allocate_pack` admits in `(priority, id)` order, so the placement is
decided by the allocator rather than by a sentence a model may ignore. The
section is non-droppable and non-compressible for two failures Rung 6 already
paid for: a dropped section leaves no header, so a problem whose criticisms the
budget cut would be byte-indistinguishable from one with none; and a compressible
one can lose its middle while still looking present.

The reader walks **both** criticism channels. That is the load-bearing decision
of the whole tranche: `observe_only` is the authority mode that cannot mint a
warrant, so the 196 attacks W2 measured produced no attack edge at all. A channel
reading `state.att` alone would have passed every other test in this tranche and
shipped around the defect it exists to close.

**C2 — submission requires discharge.** A candidate carries typed discharges
(`revised`, `rebutted`, `departure_declared`). A submission with undischarged
handles is returned ONCE with the open list and then ACCEPTED with a typed
disclosure. **There is no verdict that refuses** — the vocabulary itself is the
promise, and the test asserts over the vocabulary rather than today's two values
so a future third verdict cannot quietly become a gate. The re-ask is not a
repair grant: repair fixes a reply the SCHEMA rejected, and a re-asked reply is
schema-valid, so it consumes no repair budget and re-enters `conj()` on the
recursion shape `_context_expansion_index` already uses — no new provider call
site exists.

**C3 — the law line.** Discharge constrains how content is GENERATED and never
what counts as EVIDENCE. Pinned four ways and mutation-proved: wiring a discharge
import into `adjudication/support.py::final_labels` turns the pin RED and
restoring turns it green (`proof/c3_red.txt`).

---

## 2026-08-26 — segment 2: the instruments

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **4231 passed, 6 skipped, 0 failed** (56 of them this tranche's) |
| `python tools/docs_verify.py` (FULL) | **3 failed** — the pre-existing `CON-run-identity` shallow-clone failures, equal to the step-1 baseline |
| `python tools/docs_verify.py --audit` | **0 findings** — no check this tranche added is one that cannot fail |
| `python tools/docs_verify.py --links` | 0 dangling references, 65 documents |
| `python scripts/wheel_smoke.py` | PASS, "exact MCP schemas", pins unmoved |
| `python -u scripts/wheel_operational_smoke.py` | PASS, **80 qualification calls** — unchanged |
| `python tools/diff_budget.py --paths src/ --ceiling 960` | `WITHIN`, 943 |
| `python tools/blast_radius.py` | one granted contact; no drift at any step |
| `diff proof/digest_before.txt proof/digest_after.txt` | **empty, exit 0** |

The frozen-surface grant's acceptance check is that last line, not the suite:
every schema version's `source_config_hash` and the qualification subject digest
are byte-identical across the change. Without the `data.pop` the mutation record
shows all of them moving (`proof/granted_contact_mutation.txt`).

---

## 2026-08-26 — segment 3: What this does NOT establish

*Accepted does not mean true, and delivered does not mean effective.*

1. **F1 claims DELIVERY, not RESPONSE.** The measurement shows a RESPONSIVE
   writer couples above placebo when the channel is on and cannot when it is
   off. That is a property of the plumbing. It is not evidence that a live
   provider model responds to what the channel shows it, and Q1's finding
   forbids assuming it: a pack's own claim to have honoured a standing
   instruction is the least reliable artifact in the trajectory.
2. **The live four-arm A/B remains the proof, and is PARKED as P2.** It must be
   four arms, not three — no-critique, vacuous-critique, real-critique-as-advice,
   real-critique-in-context — because without the vacuous arm a working critic
   cannot be told from argument-shaped text. The upcoming P-C2 rematch will bear
   on this but does not replace P2's design.
3. **The stub writer is responsive BY CONSTRUCTION.** It answers the CITED SPAN
   the render carries. That is the honest content of the claim — a writer that
   responds can only respond to what it is shown — and it is why the off arm is
   the informative half: there, a perfectly responsive writer still cannot
   couple.
4. **W2's exposure census is INAPPLICABLE to these roots** and reports zero in
   BOTH arms. It reads `workflow-context-exposure-v2` records that only the v6
   workflow path writes. The JSON field is named
   `exposure_census_inapplicable` so no later reader quotes it as a finding.
5. **"Helped 6 of 6" uses W2's FALLBACK measure**, survival (the next candidate's
   final status is ACCEPTED), not the exact checker it used on P-C1. It says the
   coupled candidates survived. It does not say they were better in a sense this
   run has any scale for.
6. **The channel ships OFF.** `Config.DISCHARGE_POLICY` defaults to `"off"`;
   turning it on by default is a Config DEFAULT and belongs to F3. Nothing in
   this tranche changes what any existing run does.
7. **A kind needing a field outside `note`/`where` is a wire change, not a
   declaration.** That is the honest edge of the modularity claim, recorded as
   PARKED P3 rather than left to be discovered.
8. **No live run.** Every number here is offline.

---

## 2026-08-26 — segment 4: what the gates caught, which is the useful part

Four things were found by instruments rather than by reading, and each would
have shipped silently:

- **The signal contract refused three undeclared signals.** An operator design
  law from 2026-08-14, in documents this tranche never touched, blocked the
  channel's three Measures until each was DECLARED. This is what took `src/`
  from 899 to 943 and forced the second ceiling ruling.
- **A check of mine was vacuous, and a mutation proved it.** The granted
  contact's rider-(d) check asked whether the source CONTAINS the four-space
  pop line; an eight-space guard-scoped pop contains that string as a
  substring, so the check passed on the one arrangement the rider forbids. The
  digest check caught the same mutation while the structural one did not — two
  instruments disagreeing was the finding.
- **The architecture test caught a real design consequence.** Deriving the wire
  enum from the registry made `llm/contracts.py` a second consumer of the
  interface, so the pinned consumer list of one was wrong. It was corrected to
  the truth rather than bent to fit — and that same pin later fired
  independently during the modularity mutation.
- **The coupling instrument read 0.0 on BOTH arms at first**, which would have
  read as "the channel does nothing". Three faults, all in the instrument: a
  space after `predicate:` that failed every verdict through `ast.parse`; a
  placebo that was undefined with a single respect; and respects interleaved
  when W2's `next_candidate` is root-wide. The last is the one worth carrying
  forward: **a borrowed instrument carries the assumptions of the runs it was
  written for.**

One discipline failure of my own, recorded because it would have cost a fresh
session six steps: CHECKLIST.md's `State:` line was stale from step 7 to step
15, because three edits used multi-line patterns against a single wrapped line
and `str.replace` returns the string unchanged rather than failing. Only the
edits carrying an `assert` were caught.

---

## The instruments, all committed and re-runnable

    python experiments/2026-08-26-change-f1-discharge-criticism-channel/digests.py
    python experiments/2026-08-26-change-f1-discharge-criticism-channel/coupling.py out.json
    python -m pytest tests/test_discharge_*.py -q
    python tools/docs_verify.py && python tools/docs_verify.py --audit --links
    python tools/diff_budget.py 4760a32ef --paths src/ --ceiling 960
