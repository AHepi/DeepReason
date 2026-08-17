# Lessons learned — DeepReason, through 2026-08-17

A transferable sheet. Each lesson states the rule, then the recorded
incident or ruling that taught it. Nothing here is theory: a lesson with
no incident behind it did not make the list. Written for anyone starting
a sibling project (a new harness, a new engine, a new repo) who wants
the scar tissue without the scars.

---

## 1. Evidence and the record

**1.1 Type everything meaningful; prose is never evidence.**
Stops, denials, refusals, budgets, capability lifecycles — all typed
records in an append-only log. A run is judged only on typed outcomes
(state, stop_reason, audit JSON, replay validation), never on what the
model said about itself. This is the single decision the whole project
leans on: every diagnosis below was possible because the answer was in
a typed record, not in prose.

**1.2 Read the diagnostic artifact before theorising.**
Both cycle-0 run deaths were misattributed on first reading; in both
cases the verbatim error blob said exactly what was wrong (jolt:
"simulation observables must be plain identifiers" — a plain schema
pattern, not the exotic cause first written up). Rule: the blob first,
the theory second, the code third. A recurrence-check against known
traps is the cheapest diagnosis available.

**1.3 "Accepted does not mean true."**
Statuses are computational outcomes of criticism, not verdicts about
the world. Every results narrative records the residue — what remains
unproven — and a negative or inconclusive result is recorded as one.
Honest ledgers survived model upgrades, container rollbacks, and
doctrine changes; optimistic summaries would not have.

**1.4 Derive state; never store verdicts.**
Labels, marks, and frontiers are recomputed from the log on replay,
never persisted. When the doctrine changed (statuses renamed, triggers
deleted), nothing stored had to be migrated — only readers moved. This
also made every "did it really happen" question answerable by replay.

**1.5 Corrections are append-only too.**
`docs/ERRATA.md` is a ledger of claims already found wrong, so nobody
re-trusts them. An erratum names the document, the wrong claim, and the
evidence. Three same-day numbering collisions taught the sub-rule:
check the ledger tail for the next free number before minting one.

---

## 2. Documentation that cannot rot

**2.1 Authenticate documents by re-derivation, not authority.**
Every load-bearing claim in the map carries a `check:` shell command
that must exit 0. A signature proves who wrote a sentence; a passing
check proves the sentence is still true — the property that actually
decays. The verifier refuses checks that cannot fail (`--audit`): a
check that always passes is decoration, and decoration gets deleted.

**2.2 The map moves in the same commit as the code.**
A separate "update docs" commit is the commit that gets dropped. Map
documents (subsystems, concepts, seams, invariants, recipes) are part
of the diff or they are already stale. `Verified-at:` stamps advance
only when the checks were actually re-run — a stale stamp is honest, a
false one is not.

**2.3 Write seams, not just subsystems.**
For a change spanning two things, the seam document (how exactly they
meet, and which small fraction of each side is involved) is read BEFORE
either subsystem. It is usually small and it prevents the expensive
mistake: scoping a change by grepping 125k lines instead of reading the
one page that says where the boundary is.

**2.4 Traps are never deleted.**
Every fixed defect earns a `Traps` entry naming its run id; when fixed,
the entry is rewritten to say so — never removed. The trap list is the
project's immune memory: the manifest-sha "defect" of 2026-08-16 was
closed in one window largely because prior traps had recorded how
content-address coupling behaves.

**2.5 Read frozen surfaces before designing, not after coding.**
An explicit, short list of surfaces that must not move (digests, event
application, record formats) is read at design time. Discovering a
frozen surface after the code is written is the expensive order.
Corollary: prompts pre-grant scoped exceptions explicitly ("surface 4,
model AND validator together") so a window neither stalls nor trespasses.

---

## 3. Workflow as skills

**3.1 Route all substantive work through a phased workflow.**
Three families: defect (goal → diagnose → reproduce → propose →
implement → verify), change (capture → spec → plan → execute-one-step →
validate → deliver), audit (read-only findings). The phases exist to
prevent scope creep, missed steps, and forgotten inputs — and they did:
the recorded failures happened where a phase was skipped, not where one
was followed.

**3.2 One tranche, one goal; park everything else.**
A defect found mid-change is PARKED with a ready-to-send prompt, not
fixed. A wish found mid-defect is parked, not implemented. The parked
prompt costs the operator a paste, not an authoring session. This
cross-routing law is what kept 27-commit tranches reviewable.

**3.3 The request ledger is verbatim, and everything traces to it.**
The operator's words are captured exactly (REQUEST.md), split into
numbered requirements, and every later artifact cites requirement
numbers. Delivery is a requirement-by-requirement reconciliation with
pasted proof per row, closing with "none not-done." Drift becomes
visible because there is a fixed text to drift from.

**3.4 A test never seen red proves nothing.**
Mutation proof: break the guarded thing once in a scratch copy, watch
the test fail, restore, paste both runs. Required for every regression
test guarding a deletion or an invariant — deletions especially, since
their tests pass vacuously. This caught real vacuous tests before they
shipped.

**3.5 Skills get a dedicated workflow only after recorded failures.**
The tripwire: write a recipe (a checklist document) first; a workflow
skill is authored only after TWO recorded recipe failures. This kept
the skill set small enough to maintain and stopped speculative process
engineering.

**3.6 Rate workflows for the cheapest model that can run them.**
The audit family was deliberately written so every step is a command,
a paste, or a baseline comparison — no judgment calls — so inexpensive
models can run it. Design the workflow around the weakest intended
operator, and the strong ones get it for free.

---

## 4. Testing and gates

**4.1 Iterate on the ring, gate at the boundary.**
Run the affected test files while iterating; the full suite only at a
phase boundary. Recorded mistake: one tranche ran the full ~8-minute
gate four times in a day (~44 minutes) to learn about ~40 tests,
with `--lf` available and unused. Preserve results; re-derive only what
moved.

**4.2 0 failed is the only acceptable gate result.**
Never weaken an assertion to get green. A fixture that depended on
defective behavior may be minimally updated only when the fix's design
doc predicted it. When a baseline census became irrelevant, the test
was deleted by explicit operator ruling — not re-baselined quietly.

**4.3 Keep a baselines file for every instrument.**
Expected outputs (gate counts, known-flaky tests, known pre-existing
failures, sweep scope) live in one committed file. An audit compares
against it: delta = finding, match = baseline. The file moves only in
the same commit as whatever moved the value. This is what lets a cheap
model audit honestly — and what stopped a fresh window from
"diagnosing" the three known shallow-clone failures ever again.

**4.4 Tell the next window what is already broken.**
Every prompt now carries a "known current state" paragraph naming
pre-existing flaky failures so the window doesn't burn hours
misattributing them to its own change. The embedder tranche proved the
pattern in reverse: it found a flaky pre-existing smoke failure, proved
it pre-existing on a clean worktree, and parked it instead of chasing it.

**4.5 Instruments no gate runs will drift; pin them and say who re-pins.**
The wheel smokes (public surface pins) are run by no test gate, so any
commit changing that surface must update the pins in the same commit.
Multiple "smoke is behind again" incidents until the rule — all pins,
same commit, named in prompts — was made explicit.

**4.6 Budgets with typed stops beat judgment calls.**
Diff-size ceilings per tranche with a typed STOP on exceed. The
embedder tranche hit its ceiling (324 vs 301 insertions), stopped,
asked, and the operator raised it with no scope change — a 2-minute
decision instead of an invisible scope expansion.

---

## 5. Operating agents (the monitor/executor split)

**5.1 Separate the orchestrator from the executors, strictly.**
The monitor reads, reviews, merges, and writes prompts; it runs
nothing. Executor windows run everything and commit evidence. Operator
ruling, verbatim: "You are orchestrator. You do not run anything except
read." Review is against commits, never against claims in chat.

**5.2 A prompt is a contract: setup, authority, scope, gate.**
Every executor prompt carries: exact fetch/branch/anchor-commit setup
(so a stale container is detected immediately), the operator's verbatim
words as authority, an ordered scope with per-item proof obligations,
pre-granted frozen-surface exceptions, and the gate with baselines.
Prompts are delivered as ONE fenced code block — easy to paste whole
(operator request, 2026-08-11).

**5.3 Anchor commits detect stale checkouts.**
`git merge-base --is-ancestor <anchor> HEAD || re-fetch` in every
setup. Containers roll back silently; two windows stalled on stale
checkouts before this line existed in every prompt.

**5.4 Sequence conversions before the tests that assert them.**
When a change alters a surface AND a test must pin a law over that
surface, convert first, then write the test over the converted surface
— in one window, in strict order. A test written before the conversion
asserts the wrong layer and breaks when the conversion lands. (The
operator caught this ordering error in review; the reasoning is now in
every such prompt.)

**5.5 The tree wins arguments.**
When a reviewer (including the monitor) asserts something about the
code, the window verifies against the tree and the tree's answer
stands. Recorded case: monitor claimed a loop was already removed; the
window proved from the tree it was scheduled two rungs later; the
monitor owned the error. Symmetrically: an external reviewer's "the
advice was wrong" was later withdrawn when a census found a live
producer — kept struck-through in the plan, because the reasoning
failure (compatibility question vs liveness question look alike) is
the reusable part.

**5.6 Census before deletion.**
Before deleting any symbol, count its producers and consumers fresh —
do not trust the design doc's belief. The enum member scheduled for
deletion turned out to have a second live producer nobody had counted;
deleting it would have dragged a whole subsystem into a tranche meant
to ship alone.

---

## 6. Environment

**6.1 Assume the container is hostile.**
Cloud containers roll back silently, killing processes and deleting
gitignored files. Therefore: commit and push at every phase boundary;
snapshot loops during long runs; after any gap, verify the head and
re-sync before trusting anything local.

**6.2 Pay large downloads visibly, in setup.**
The neural embedder's ~523 MB weights are fetched by an explicit
warm-up command in the setup phase — never silently inside cycle 1
where the cost is invisible and a rollback wipes the cache anyway.
General form: any expensive lazy initialization gets an explicit,
idempotent, visible warm-up step.

**6.3 Silent fallbacks must be loud where operators look.**
Runs degraded to hash embedding for weeks with the fallback recorded
in a typed measure "read by nobody." The fix was not just the install:
the fallback now prints in the results surface and the terminal
summary. A typed record nobody reads is not yet a disclosure.

**6.4 Deterministic identity; retire, never edit.**
Same inputs → same run id; a leftover root refuses relaunch. Retire by
renaming (and commit the rename FIRST), never by editing a committed
root. To change a question without losing state, append an amendment
epoch. Editing history was never once the right answer.

---

## 7. Communication with the operator

**7.1 Answer the worry first.**
The first sentence answers what the operator actually fears, before
any mechanism. When a finding sounds like bad news, state what it does
NOT mean for their intent before what it does.

**7.2 Gloss every technical term, inline, every intermediary message.**
The precise term plus, in plain words, what it is and does. When
unsure whether a term needs glossing, gloss it. Internal artifacts
keep full precision; anything operator-facing carries its
plain-language meaning alongside.

**7.3 Price forks in the operator's terms, with a recommendation.**
Present decisions as real-world roads: what they can do, when, at what
cost. Never an option list without a recommendation. Never re-litigate
a decision already made.

**7.4 Own errors plainly and move on.**
"The tree wins" corrections are stated in one sentence, without
hedging, and without restating the reasoning that produced the finding
once the finding is stated.

**7.5 Ledger the operator's design decisions verbatim, dated.**
Standing laws are recorded in the operator's exact words, with
supersessions noted explicitly when a later statement overrides an
earlier one in the same exchange. This ended repeated re-litigation
("do not make them repeat it again") and let every later window cite
authority instead of guessing intent.

---

## 8. Design-law governance (the meta-lessons)

**8.1 Disclose, never die.**
Compile-time refusals of parseable configurations became typed
disclosures recorded alongside the result; impossibility surfaces at
the point of use, typed. Refusal is reserved for parse/shape errors —
things that are not configurations at all. The system got simpler and
the operator stopped being blocked by other people's caution.

**8.2 One path, not two paths kept in agreement.**
When two launch paths drifted (one had lifecycle operations, one did
not), the fix was not synchronizing them — it was deleting one. Parity
by construction: there is nothing left to diverge. Any "keep them in
agreement" design is a drift generator with a delay.

**8.3 Interfaces are contracts keyed to instances, not wirings.**
The signal registry lesson: consumers read a declared interface (name,
unit, semantics, staleness bound), keyed by seat instance rather than
role, so future topologies add signals by declaration instead of
teaching a consumer about a subsystem. Layer changes explicitly:
FROZEN protocol, VERSIONED registry/policy, FREE parameters.

**8.4 Retire compatibility deliberately, and scope the retirement.**
"Old runs owe the future nothing" retired cross-version replay
obligations — but the law's own text states the scope boundary:
within-version integrity is the epistemology and is untouched. A
sweeping law without its boundary sentence would have been over-read
within a week (it nearly was, at Rung 3a).

**8.5 Efficiency may never touch evidence.**
Allocation, throttling, render slices, and diagnostics act only
through attention and budgets; no signal and no allocation decision
may reach a label or a warrant. Provenance may inform attention;
appraisal may not read it. This single boundary sentence has vetoed
more bad designs than any other rule in the project.

**8.6 Prefer generated evidence over built machinery.**
Operator law, verbatim: "Ollama API tokens are cheap, you are not."
When a question can be answered by live runs or API experiments, run
them instead of reasoning it out or building synthetic fixtures —
with pre-registration and raw preservation unchanged. Several designs
were settled by an afternoon of runs that would have cost days of
construction.
