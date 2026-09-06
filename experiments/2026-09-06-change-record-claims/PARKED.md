# Parked — found in this tranche, deliberately not done here

## P1 — the appraisal LABELLING rule, for the UNDECIDED-premise fork

**Readiness in DeepReason is read from the record — warrant checks, judge
verdicts, criticism dispatch — never marked by a person.** That is the whole
reason this is parked as one half of a mechanism rather than adopted whole.

WHAT: the operator's other harness carries a second layer beside its claims
mechanism, `src/creib/forge/conformance/appraisal.py` (clone at
`/home/user/h-epi`, head `f97239fc38f52b664fb56ad518a8ac60ac959482`; read-only,
never vendored). It does two separable things:

1. A **labelling rule** over a finite argument graph. An argument is `in` when
   it is ready, every argument essential to it is `in`, and every argument
   attacking it is `out`; `out` when it is not ready, or an essential argument
   is `out`, or an attacker is `in`; `undecided` otherwise. The labels are the
   least fixed point of those two rules from empty sets, reached in at most
   twice as many rounds as there are arguments, and the code raises rather than
   guessing if it is not, or if an argument would be both `in` and `out`. A
   mutual attack with nothing outside it stays `undecided`; a support cycle
   does not bootstrap itself into `in`; a criticism of a criticism restores the
   reading it defended.
2. A **readiness input taken from a person**: each argument carries `PASS`,
   `FAIL` or `UNKNOWN` that someone wrote into the file by hand.

The SECOND is rejected outright. The operator, 2026-09-06: "Actually that
ruling was old", "no the rule from the other harness". Under the ungated-seats
law (2026-08-28) whether a criticism carries authority is the harness's own
decision, made by its rules, judges and configuration with no person in the
loop. Nothing in this repository may grow a human-readiness step.

The FIRST is worth reading, and it has a live home. DeepReason already has the
question the labelling rule answers, open and parked:
`experiments/2026-09-05-criticism-premise-declaration/PARKED.md` **P4 — an
UNDECIDED essential premise still leaves its target refuted**. Today a
criticism whose essential premise is neither refuted nor established goes
`suspended_unsupported` while the attack it contributed still stands, so its
target stays `refuted`. Open Inquiry 1.1 §11.3 says an undecided essential
premise should prevent its dependent from becoming in — which is, in different
words, the labelling rule's own second clause. The appraisal module is a
worked, tested implementation of "undecided underneath means contested",
including the fixed-point termination bound and the raise-rather-than-guess
behaviour when the graph is inconsistent. It is a reference to read before
designing, not a design to copy: its arguments are readings supplied by a
person, and DeepReason's would be warrants, judge verdicts and criticism
dispatch declarations the record already carries.

WHY NOT HERE: P4 is a DEFECT in `src/deepreason/adjudication/` pass order, and
this is a change tranche whose scope holds `src/deepreason/` byte-untouched.
Changing how a Status is derived from edges reinterprets every recorded root,
which is the reason P4 was written as DESIGN-AND-STOP in the first place.

Ready-to-send prompt:

```
EXECUTOR WINDOW — DEFECT TRANCHE, DESIGN AND STOP: an UNDECIDED essential
premise does not protect its dependent's target the way a refuted one now does

Read CLAUDE.md IN FULL. Load deepreason-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at dr-set-goal.
Offline; no key.

BEFORE ANYTHING ELSE, so you do not build the wrong half: readiness in
DeepReason is read from the record — warrant checks, judge verdicts,
criticism dispatch — and is NEVER marked by a person. The operator ruled that
out on 2026-09-06 ("no the rule from the other harness"), and the ungated-seats
law (2026-08-28) says the same thing positively: whether a criticism carries
authority is the harness's own decision by its rules, judges and
configuration. Any design that adds a human-readiness field, file or flag is
refused before it is read.

THE SYMPTOM, already reproduced and already committed as a test:
  python -m pytest tests/test_criticism_premises.py -k undecided -q
It PASSES today, and what it asserts is the defect — A refuted, K suspended,
M suspended, C suspended_unsupported. Paste those four labels into GOAL.md.
The audit's own fixture is
experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/check11_da1_vs_harness.py
(F2); run it and paste its table too. Full context:
experiments/2026-09-05-criticism-premise-declaration/PARKED.md P4.

THE RULE IT BREAKS: Open Inquiry 1.1 §11.3 — "an undecided essential premise
prevents its dependent from becoming in". The criticism C is correctly NOT in
(it is suspended_unsupported), but the attack it contributed still stands, so
A stays refuted.

A REFERENCE WORTH READING BEFORE YOU DESIGN, for the labelling rule ALONE:
clone the operator's other harness read-only
(git clone https://github.com/AHepi/h-EPI /home/user/h-epi) and read
src/creib/forge/conformance/appraisal.py plus docs/how-it-works.md section
"Readings under criticism". Take the LABELLING RULE only: in when ready and
every essential argument is in and every attacker is out; out when not ready
or an essential is out or an attacker is in; undecided otherwise; least fixed
point from empty sets; a termination bound of twice the argument count; and a
raise rather than a guess when an argument would be both in and out. Its
test_labelling_policy fixes the three cases worth checking — a mutual attack
stays undecided, a support cycle does not bootstrap itself, and a criticism of
a criticism restores the reading it defended. DO NOT take its readiness input,
which comes from a person, and do not vendor or import any of its code. In
DeepReason the inputs to the same rule are what the record already carries.

WARNING, READ BEFORE DESIGNING: this one almost certainly IS in
src/deepreason/adjudication/ — pass order between the grounded extension and
the support cascade. That is not a frozen surface, but it is the module the
2026-09-05 tranche was explicitly forbidden to touch, and
CON-warrants-and-attacks.md states the current rule as law with passing checks
("refuting a premise never refutes its dependents: pass 2 gives them
SUSPENDED_UNSUPPORTED, because orphaned is not false"). Changing how a Status
is derived from edges REINTERPRETS EVERY RECORDED ROOT — the map's own "Where
to change what" table says so.

END STATE: DESIGN AND STOP. FIX.md carries the pass-order change, its blast
radius from tools/blast_radius.py, what it does to committed roots, and how
the labelling rule's inputs are read from the record rather than declared.
Then STOP for the operator before writing any code. Do not implement on your
own reading.
```

## P2 — the record types no countercondition, and no proposal provenance

WHAT: `experiments/2026-09-06-change-writers-room-organiser-testing/PREREG.md`
predicted "every countercondition registered came from a room proposal". The
record cannot decide it. `countercondition` occurs in the ARM R root only
inside `artifact.data.content_ref` prose (13 artifacts) — there is no typed
record of a countercondition being registered, and none of the proposal it
came from. The nearest typed thing is the evidence-citation check emitted at
`src/deepreason/rules/conj.py:2468`, which says whether a candidate's
references resolve to admitted blocks and whether its quotes match. This
tranche's `ORG-COND-01` uses that as a declared PROXY and says so in its own
note; the claim can be refuted, it cannot be confirmed.

Not fixed here: this tranche holds `src/deepreason/` byte-untouched, and
typing a new observable on the conjecturer's output is a change to what a run
records, not a change to a reading instrument.

Ready-to-send prompt:

```
EXECUTOR WINDOW — CHANGE TRANCHE: a candidate's counterconditions should reach
the record as structure, not as a sentence inside its own prose

Read CLAUDE.md IN FULL. Load dr-change-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at
dr-capture-request with this message as the operator's words. Offline.

THE FACT, measured: in the ARM R root
experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/
run-36d9a22c3e2045ae1b8c7bfb9d95d092, the word "countercondition" appears only
inside artifact content prose. Reproduce it:
  grep -rlo countercondition <that root>/objects/ | wc -l
A candidate declares what would refute it, and the record keeps that as text
inside a content address. Nothing downstream can read it: not the scheduler,
not an audit, not tools/record_claims.py, which had to fall back to a citation
proxy (see that tranche's claims.json, ORG-COND-01, and
experiments/2026-09-06-change-record-claims/PARKED.md P2).

ONE GOAL: a candidate's refutation conditions reach the record as typed
structure on the artifact's own interface, each carrying the evidence
reference it rests on where it has one, so a claim about where a
countercondition came from can be tested instead of proxied.

WATCH: the artifact's content is its content ADDRESS. Anything that changes
the prose changes ids for runs that would have produced them — a FUTURE-run
change, which is ordinary work, but say so in SPEC.md and check no committed
fixture or pack golden pins the string. Read INV-reference-menu.md before
choosing a ref role: the menu owns every legal handle set and may never decide
validity. Read CON-conjecture-source.md for the socket this lands on.

END STATE: the new structure is readable from the record, an added claim in
that tranche's claims.json tests the real statement rather than the proxy,
full gate 0 failed, docs_verify 0 failed.
```

## P3 — `.claude/skills/README.md` does not exist

WHAT: the executor brief for this tranche asked, as a setup step, to read
`.claude/skills/README.md`. There is no such file: `ls .claude/skills/` lists
26 skill directories and nothing else. Recorded in REQUEST.md as C3 and in
SPEC.md as A4 rather than silently skipped.

Not fixed here: writing a README nobody asked for would be inventing an
artifact, and whether the skills directory wants an index is the operator's
call, not an executor's. If the brief's step was meant to point at
`CLAUDE.md`'s own "Which workflow to use" section, nothing is missing at all.

No prompt: this is a question for the operator, not a tranche.
