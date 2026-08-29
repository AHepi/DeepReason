<!-- DR-SCHEMA -->
Verified-at: 9ae772e6
Verify: python tools/docs_verify.py --self-test

# The map schema — how to read these documents, and how to change them

`docs/map/` is a navigation layer over `src/deepreason/`. It exists so that a
large change ("change how schools interact with the scratchpad") can be scoped
by reading a few files instead of by reading 125 000 lines.

**It is a map, not a spec.** `docs/harness-spec-*.md` says what the system ought
to do. This says what the code *is* and where it lives. When the two disagree,
the code is what the map must describe, and the disagreement is itself worth
recording.

## The one rule

**Every load-bearing claim carries a check that a machine can re-run.**

A claim without a check is an opinion, and opinions go stale silently. A claim
with a check is falsifiable: `tools/docs_verify.py` re-runs every check in every
document and fails on any that no longer holds. That is what authenticates a
document — not a signature, and not the fact that someone once wrote it down.

## File naming, which is also the ID grammar

One flat directory. The filename IS the identifier, so `ls docs/map/` is the
whole table of contents and `grep -rl DR-SEAM-rules-x-scratch docs/` finds every
reference.

| Prefix | Means | Example |
|---|---|---|
| `SUB-<pkg>.md` | One subsystem: what it owns, its entry points, its state | `SUB-scratch.md` |
| `SEAM-<a>-x-<b>.md` | How two subsystems meet. `<a>` and `<b>` alphabetical | `SEAM-rules-x-scratch.md` |
| `INV-<slug>.md` | An invariant or frozen surface, and what breaks if violated | `INV-frozen-surfaces.md` |
| `CON-<slug>.md` | A cross-cutting concept that is not a package | `CON-schools.md` |
| `REC-<slug>.md` | A change recipe: given a goal, the ordered path through the map | `REC-change-a-seam.md` |

`CON-` exists because the hardest changes are not package-shaped. "Schools" is
not a directory — it is a concept spread across `schools.py`, `run_manifest.py`,
`workflow/`, `rules/` and `llm/`. Without concept documents, the question
"how do schools interact with the scratchpad?" has no home, because neither side
of it is a package. A seam may join any two IDs, concept or subsystem:
`SEAM-schools-x-scratch.md` is `DR-CON-schools` meeting `DR-SUB-scratch`.

Inside each file the first line is an HTML comment holding the canonical ID:
`<!-- DR-SUB-scratch -->`. IDs are `DR-` prefixed so a grep for `DR-SEAM-` never
collides with prose. Cross-references use the bare ID, never a relative path —
paths break when files move, IDs do not.

`Seams:` may name only documents that EXIST. A seam that has been identified
but not written goes in `Seams-undocumented:` as a plain pair (`rules x
workflow`), deliberately without a `DR-` prefix so `--links` cannot mistake it
for a document. This keeps the identification — which is real analysis, and
expensive to redo — without letting a reference promise a file nobody wrote.
`python tools/docs_verify.py --links` enforces it.

**Seams are the point.** Most large changes are seam changes: the work is not
inside one subsystem, it is in how two of them agree. A subsystem document that
does not name its seams has not finished.

## Anatomy of every document

    <!-- DR-SUB-scratch -->
    Verified-at: <short commit the claims were last checked against>
    Verify: <one shell command; must exit 0>
    Owns: <the files this document is authoritative for>
    Seams: <DR-SEAM ids this subsystem participates in — MUST all exist>
    Seams-undocumented: <plain pairs, no DR- prefix, for seams not yet written>

    # <Human title>

    ## What it is            -- 3-6 sentences, no code
    ## Entry points          -- the functions an outside caller actually calls
    ## State it owns         -- what persists, and where
    ## Invariants            -- DR-INV references, not restatements
    ## Where to change what  -- a table: "to do X, edit Y, test Z"
    ## Traps                 -- things that have actually gone wrong here

### Checks

Any claim that could rot gets a trailing check on its own line:

    The criticism rule never receives scratch context.
    `check: ! grep -q "deepreason.scratch" src/deepreason/rules/crit.py`

    formally_backed is a superset of execution_backed.
    `check: pytest tests/test_prose_refutation_boundaries.py -k formal_backing -q`

A check must start at **column 0** — that is what lets the worked examples above
sit inside an indented block without the verifier trying to run them.

A check MAY SPAN SEVERAL LINES. It opens with a `check:` span at column 0 and
closes at the first later line whose text ends with a backtick. The newlines
between are part of the command, so a `python -c` body keeps its statements:

    Cascade integrity re-frames the fallen problem's own scope, once.
    `check: python -c "
    import inspect
    from deepreason.invariants import verify_root
    block = inspect.getsource(verify_root)
    assert '_framed_problem_ids(h, fallen.scope)' in block
    "`

The grammar is TOTAL: at column 0, `check:` opens a check or an ERROR — never
prose. An opener that reaches the next column-0 opener, or the end of the
file, without closing FAILS the run with an `unparseable check` line, and
`--audit` reports it beside the vacuous ones. There is no third disposition,
deliberately: a parser free to decide that an opener was "probably prose" is
how 72 checks across 27 documents went unexecuted from this instrument's first
day until 2026-08-29, while looking in the document exactly like checks that
ran — the INV- documents worst of all, because a claim strong enough to need
an invariant is usually defended by a multi-statement block.

The price of totality is one authoring rule: **never begin a line with a
quoted `check:` span you do not mean to run.** Wrap the sentence so the span
sits mid-line, or indent it.

`check: python tools/docs_verify.py --self-test && python -c "
import sys; sys.path.insert(0, 'tools')
import docs_verify as dv
multi = [(d.path.name, n) for d in dv.documents() for n, c in d.checks if '\n' in c]
assert len(multi) >= 70, len(multi)
"`

Use `python -m pytest`, never bare `pytest`: the container's PATH may resolve
`pytest` to a tool shim that cannot see the editable install, which fails a
check for a reason that has nothing to do with the claim.

A check is any shell command. Exit 0 = the claim still holds. Prefer the
cheapest command that would actually fail if the claim became false: a `grep`
that a rename would break beats a test run that takes a minute, and a test id
beats a grep when the claim is behavioural rather than structural.

### What a check can and cannot bind

A check binds a claim about STRUCTURE — a symbol exists, a module does not
import another, a behaviour holds under test. It cannot bind a claim about
HISTORY, INTENT, or WHY. "This guard exists because prose immunity must not
suppress scrutiny evidence" is unfalsifiable by grep, and it is also the most
valuable sentence in the document.

So roughly nine in ten prose lines here are unbacked, and that is structural,
not laziness. Two consequences to design around:

1. **Convert unbackable claims into backable ones where you can.** A date in
   prose cannot be checked and two documents will eventually disagree about it
   — this has already happened here. Cite the artifact instead: a tranche
   directory, a test id, a typed error code. A path is unambiguous AND
   greppable, so the same sentence becomes checkable.
2. **Treat unbacked prose as the part that decays.** `Verified-at` and
   `--stale` exist for it. When you re-read a document, the checks are already
   proven; spend the attention on the sentences no check protects.

### Check-writing rules learned by falsification (each class was found live)

Ten Opus falsification passes over the seam documents proved ~160 checks
failable and rewrote 44 that were not. Every rewrite fell into one of six
classes — write new checks against this list:

1. **Pair every negative grep with a positive anchor on the same file.** A
   missing or renamed file makes `grep` exit 2, and `!` inverts that to a
   pass; four documents had checks that passed with their subject deleted.
2. **Never bind a guard by its message string alone.** Guards gutted to
   `_authority(True, …)`, `if False:`, `or False`, or a dead `raise` kept
   their strings and passed message-greps in six documents. Pin the guard's
   AST (test + raise together) or call the code and demand the typed refusal.
3. **Substring import greps miss relative imports.** `from ..rules.spawn
   import …` walked past `deepreason.rules` greps, including on a seam's core
   dependency-arrow claim. Resolve `ImportFrom` levels via AST.
4. **Pin signatures whole and enumerate dynamically.** `**kwargs`, a renamed
   parameter, or a new sibling class (`AtomicCriticWireContractV2`) evaded
   spot-greps; pin the full parameter list, discover class families with a
   floor count.
5. **In shell checks, the last command decides.** An `A && B … ; for …; done`
   chain returns the loop's status and silently discards every conjunct — one
   document's central check was entirely dead code.
6. **Counts are claims.** `-ge N` floors hid a 6-file error and a 28-vs-29
   mismatch; when the prose states a number, the check pins it with `-eq`.

And one measurement rule: **stale `__pycache__` survives a revert.** A
falsification pass produced a phantom test failure with `git status` clean
because bytecode outlived the reverted source. Clear `__pycache__` before
trusting any measurement taken near a mutation window.

A `Sweep:` header must target ENFORCEMENT (sites that compare or raise on the
field), not readers. When every candidate spec flags only readers — it happens;
`SEAM-evaluation-x-ontology` is the recorded case — leave the header off and
say why in the body rather than shipping a spec that cries wolf.

**Do not write a check that cannot fail.** A check reading `check: true` is
worse than no check, and so is `check: test -f src/deepreason/harness.py`:
both buy the claim false credibility. `tools/docs_verify.py --audit` flags checks
that pass against a deliberately mutated tree.

## How to READ the map

Start at `INDEX.md`. It routes; it does not explain. Then, by task shape:

- **"Where does X live?"** → `INDEX.md` routing table → the `SUB-` document.
- **"How do A and B interact?"** → `SEAM-<a>-x-<b>.md`. If it does not exist,
  that is a finding: either the two do not interact, or the map is incomplete.
  Check `INDEX.md`'s seam matrix before concluding either.
- **"Can I change this?"** → `INV-frozen-surfaces.md` FIRST. Some surfaces are
  not yours to change, and finding that out after writing the code is expensive.
- **"How do I make a change of this shape?"** → the matching `REC-` document.

Read the seam before the subsystems it joins. The seam document says which parts
of each subsystem the change actually touches, which is usually a small fraction
of either.

## Triage: is a change isolated, or does it need REC-change-a-seam?

Before scoping ANY change to a file under `docs/map/`'s charter, decide which
kind of change it is — the two need different care, and treating a seam
change as isolated is how a correct pair of subsystem documents ends up next
to a stale seam between them (`docs/map/REC-change-a-seam.md`'s own Traps
section names this as the recurring mistake).

**The rule, mechanical and decidable:**

    A change to file F (or symbol S in F) is SEAM-GUIDED if either holds:
      1. F or S appears in any SEAM-*.md document's "Where it is expressed"
         table (grep every docs/map/SEAM-*.md for the file/symbol name).
      2. F is named in the `Owns:` header of TWO OR MORE SUB-/CON- documents.
    Otherwise the change is ISOLATED: edit F and the ONE document that owns it.

Rule 2 exists because `Owns:` overlap is itself evidence of a seam even before
anyone has written the seam document down — a file two documents both claim
authority over is a file where an undocumented agreement already lives. This
is exactly the shape `docs/map/REC-change-a-seam.md` Step 1 assumes has
already been done ("name both sides as IDs") — this triage is what to run
BEFORE that recipe, to decide whether it applies at all.

`check: python3 -c "import glob, re; owners = {}; [owners.setdefault(p.strip(), []).append(f) for f in sorted(glob.glob('docs/map/SUB-*.md') + glob.glob('docs/map/CON-*.md')) for m in [re.search(r'^Owns: (.*)$', open(f).read(), re.MULTILINE)] if m for p in m.group(1).split(',') if p.strip()]; dupes = {p: fs for p, fs in owners.items() if len(fs) > 1}; assert 'src/deepreason/rules/conj.py' in dupes, sorted(dupes)"`

**A worked example already in this repo, both directions:**

- SEAM-GUIDED by rule 2: `src/deepreason/rules/conj.py` is named directly in
  `DR-CON-schools`'s and `DR-CON-conjecture-source`'s `Owns:` headers (the
  check below), and is additionally covered by `DR-SUB-rules`'s directory-
  level `Owns: src/deepreason/rules/` — three documents in total once
  directory ownership is resolved, so a change here follows
  `REC-change-a-seam.md`, not an isolated edit to whichever document the
  author happened to have open.
- ISOLATED: `src/deepreason/adjudication/edges.py` is `Owns:`-listed by
  `DR-SUB-adjudication` alone, and appears in no `SEAM-*.md` "Where it is
  expressed" table except `DR-SEAM-adjudication-x-rules`'s own — so a change
  purely internal to `build_att`'s fixpoint body, not touching that seam's
  named sites, is an isolated change: edit `edges.py` and
  `SUB-adjudication.md` only.

**What this triage does NOT decide:** whether a seam document needs to be
CREATED (that is `REC-change-a-seam.md` Step 7, reached only after this
triage says SEAM-GUIDED and Step 2 finds no existing document) or whether an
`Owns:` overlap found by rule 2 is itself a map defect worth flagging (it
usually is not — shared ownership of one file by a `SUB-` and a `CON-`
document is normal, e.g. `capture/schools.py` under both `DR-SUB-scheduler`-
adjacent packages and `DR-CON-schools`; three or more, as in the worked
example above, is the stronger signal).

## How to CHANGE the map

The map is part of the change, not a chore after it. A change that alters
behaviour without updating the map has left the next reader a document that
lies, which is worse than no document.

1. **Change the code and the map in the same commit.** Not the same PR, the same
   commit. A separate "update docs" commit is a commit that gets dropped.
2. **Update `Verified-at:`** to the commit you are making. If you did not check
   the document's claims, do not advance the stamp — a stale stamp is honest, a
   false one is not.
3. **Every new claim needs a check.** If you cannot write a check that could
   fail, the claim is probably too vague to be useful; sharpen it until you can.
4. **Run `python tools/docs_verify.py`** before committing. It is part of the
   gate, not an optional courtesy.
5. **Adding a subsystem** means: a new `SUB-` file, a row in `INDEX.md`'s
   routing table, and a seam document for every subsystem it imports or is
   imported by with more than incidental traffic.
6. **Choose the next seam to write by MEASURED coupling and risk, not by
   whatever the last conversation happened to mention.** An example someone
   gives to illustrate a task SHAPE is not a priority ranking. This rule exists
   because it was broken: a seam named in passing was written up as "the
   flagship" while `llm x workflow`, the second-highest-coupled pair in the
   repo, was skipped entirely. `INDEX.md`'s matrix is the ranking; a pair with
   no import count is not thereby unimportant, but it needs a stated reason
   beyond having been mentioned.
7. **Never delete a `Traps` entry** because the trap was fixed. Rewrite it to
   say it was fixed and when. Traps are the memory of what has actually gone
   wrong, and that memory is the most expensive content here to regenerate.

### Completeness is the failure mode checks cannot catch

Every check in a seam document can pass while the document is still WRONG by
omission. A check proves the sites listed are real; nothing proves the list is
complete, and an implementer who trusts an incomplete list ships a change that
misses a guard.

This has already happened. `SEAM-schools-x-scratch` named five enforcement
sites and every check passed. A mechanical sweep — every file mentioning
`school_id` alongside a conjecture-context symbol, filtered to those that
actually COMPARE or RAISE on it — found a sixth, in `harness.py`, a frozen
surface. The document said "caught four more times"; it was five.

The sweep is now a tool mode, so completeness no longer depends on anyone
remembering to run it. A seam document declares its agreement in one header
line:

    Sweep: school_id && conjecture_context|PlannedConjectureContext|scratch

Left of `&&`: the field the agreement moves. Right: the other side's symbols
(both regexes). `python tools/docs_verify.py --coverage` then flags every
source file that matches both sides AND compares-or-raises on the field but is
named nowhere in the document. Dismissal is by NAMING: a flagged file that
belongs to another seam is resolved with one sentence saying which — the rule
is not "every site gets a table row", it is "no enforcing site may be
invisible to the reader".

The header ratchets in: a seam without one is reported by `--coverage` but not
failed, and MUST gain one the next time the document is edited. On its first
run the sweep found a seventh guard (`llm/adapter.py` dispatch refusal) and an
eighth observational site (`workflow/shadow.py`) in the one seam that had
already been hand-corrected once — which is the argument for the tool over
another pass of prose.

### Do not measure the tree while a falsification pass is running

A falsification agent proves a check can fail by editing `src/` to make the
claim false, confirming the check catches it, then reverting. During that
window the working tree is deliberately wrong, and any test run, gate, or
sweep measured against it is measuring someone else's mutation.

This has already produced one false alarm: a subsystem ring reported 15
failures that did not exist — the same command returned 64 passed a minute
later, and `git status` was clean both times, because the mutation had already
been reverted by the time anyone looked.

So: run a falsification pass, or measure the tree, never both at once. If you
must overlap, give the agents `isolation: 'worktree'` so their mutations land
in a private copy — at the cost that their document edits land there too, and
have to be brought back.

### Staleness

`Verified-at` older than the file it documents is a warning, not an error —
plenty of source edits do not invalidate a description.
`python tools/docs_verify.py --stale` lists documents whose `Owns:` files have
changed since their stamp, so a reviewer can judge which actually need a
re-read. Failing checks are always errors.

## What does NOT belong here

- Narrative of a change ("we then decided to..."). That is a tranche's
  `experiments/<date>-*/` directory.
- Aspiration. If it is not in `src/`, it is not in the map. Planned work lives
  in `docs/proposals/`.
- Restated invariants. Reference `DR-INV-*` by ID; one definition, many readers.
- Line numbers in prose. They rot within days. Name the function or the symbol;
  `grep` is the address.
