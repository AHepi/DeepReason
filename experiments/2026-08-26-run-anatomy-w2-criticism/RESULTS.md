# W2 — criticism anatomy: what the attacks targeted, and whether criticism
# ever did causal work

**Tranche.** `experiments/2026-08-26-run-anatomy-w2-criticism/`, RUN ANATOMY
PROGRAM measurement tranche W2. Read-only on `src/` and `tests/`.
**Branch.** `claude/criticism-anatomy-w2-1z2029`. **Base.** `origin/main`
at `bdb516ae4`.
**Every number below is generated**, not typed: `TABLES.md` is emitted by
`tables.py` from `pr1_census.json`, `pc1_census.json`, `pr1_q5.json`,
`pc1_q5.json`, `sweep.json`. If a figure here is not in `TABLES.md`, it is
not this tranche's figure.

---

## 2026-08-26 — segment 1: the finding

**In both priority roots, criticism did no causal work, and the record says
why in one line: no criticism was ever put in front of anything that makes
the next candidate.** Across P-R1 and P-C1 ARM H, **0 of 196 LLM attacks**
were exposed to a later conjecture dispatch (`TABLES.md` §3a). Two of P-C1's
345 mechanical verdicts were. That is the whole causal channel, and it was
shut.

The second finding is what filled the gap. **Every single status a
criticism moved in either run was moved by the problem's own admission
criteria, not by anything a critic seat wrote.** All 118 attack edges in
P-R1 and all 345 in P-C1 come from demonstrative warrants minted by
commitment verdicts; **0 come from an LLM attack**, and no LLM attack in
either run carried a warrant at all (`TABLES.md` §4). Every criticism
dispatch in both runs was `observe_only` — the authority mode that cannot
mint a warrant — so this was not a near miss. In P-C1 all 345 of those
verdicts are the problem's own three criteria; in P-R1, 116 of 118.

So the anatomy is: **two organs called criticism, one of which is load-
bearing and is not criticism, and one of which is criticism and is inert.**

### The three Q5 rates, and why they must be read with their placebo

Candidates are generated in batches, so the candidate after a criticism is
usually a fresh construction, not a revision. Anything that "changes in the
criticized respect" would have changed anyway. So every rate is computed
twice — once on the candidate AFTER the criticism, once on the candidate
BEFORE it, which cannot have been influenced by it — and the difference is
the only column that is evidence.

| Root | Operationalization | n | Coupling | Placebo | **Coupling − Placebo** | Repair | Neglect |
|---|---|---|---|---|---|---|---|
| P-R1 | R1 mechanical | 118 | 17.8% | 30.5% | **−12.7 pp** | 38.1% | 82.2% |
| P-R1 | R2 prose-quote | 54 | 98.1% | 100.0% | **−1.9 pp** | 37.7% | 1.9% |
| P-C1 | R1 mechanical | 341 | 9.4% | 3.5% | **+5.9 pp** | **0.0%** | 90.6% |
| P-C1 | R2 prose-quote | 60 | 100.0% | 100.0% | **+0.0 pp** | **0.0%** | 0.0% |

Read plainly: three of the four placebo-corrected effects are zero or
negative, and the fourth (+5.9 pp in P-C1) bought nothing — **not one of the
32 coupled changes improved the score**. NeglectRate is high (82%, 91%) on
the mechanical operationalization, which is the honest complement of a
CouplingRate that is at or below chance.

### THE P-C1 QUESTION, answered

*132 candidates, criticism running the whole time, best score frozen — did
any criticism event ever precede a score improvement in the criticized
lineage?*

**No.** The exact rational checker finds exactly **two** best-score events in
the entire run: log seq 320 (score 0.0 — the first construction that was
merely valid) and log seq 1041 (0.0004075, the run's final best). After seq
1041 the run produced **67 further construction candidates under 251 further
criticism events, and not one scored above zero**. Coupled changes that
improved the score: **0 of 32** (mechanical) and **0 of 60** (prose-quote).

That single number — zero — is "does criticism steer search" for this
harness, on the only root that has a run-owned scalar to steer toward.

### TARGETS

| | P-R1 | P-C1 ARM H |
|---|---|---|
| Criticism dispatches | 112 | 175 |
| → attacked | 89 | 111 |
| → declined (`attack: false`) | 17 | 56 |
| → produced no case / unparsed | 6 | 8 |
| Mechanical commitment verdicts | 118 | 345 |

Of the LLM attacks, what they contained (the wire contract's own fields, not
a reading of the prose): names a premise 78% / 89%; offers a counterexample
36% / 25%; cites evidence 47% / 37%; quotes the target verbatim 63% / 56%;
**none of these** 3% / 8%. So "attacked nothing identifiable" is rare — the
attacks are substantive. They simply have nowhere to go.

### COMMITMENT ATTACKS, judged mechanically

Every warrant verdict was re-derived with the harness's own evaluator
(`deepreason.programs.evaluate`) on the target's own bytes:

| Root | correct | misquoted | attacked-nonexistent | unverifiable |
|---|---|---|---|---|
| P-R1 | **118/118** | 0 | 0 | 0 |
| P-C1 | **345/345** | 0 | 0 | 0 |

The mechanical channel is exactly right, every time, and the commitment it
names is in the target's interface every time. That is worth stating
plainly, because it is the good news: what moved statuses was correct.

The LLM attacks cannot be scored on those rows — they name no commitment —
so they are scored on what CAN be checked: whether the thing they quoted is
in what they were shown. **72% (P-R1) and 76% (P-C1) of quoted spans are
verbatim in the target**; 20% and 24% are in nothing the dispatch was shown.
`EXEMPLARS.md` E3 shows a one-letter miss ("merely describe" for "merely
describes") beside a wholly unlocatable one.

The evidence-citation channel is worse and more interesting. Of P-R1's 55
critic evidence citations, **5 name a real dossier block** out of 623
available, and the same 5 are the only ones that were exposed to the citing
dispatch; 62% quote the target instead, filed under a block id that names
nothing (`000000000000` among them). P-C1 had no dossier at all and its
critics emitted 51 citations anyway.

**The harness is not blind to this — it is mostly not asked.** Its own
citation checks are Measures on the log: P-R1 recorded **234 checks of
CANDIDATE evidence refs** (210 verified, 20 quote-mismatch, 2 not-exposed,
2 unknown-block) and **3 checks of CRITIC premise citations**, of 55
emitted. 95% of the critics' citations were never checked; in P-C1, 100%.

### LABEL WORK

118 / 118 and 345 / 345 attack edges from mechanical verdicts; 0 and 0 from
LLM attacks. All 463 warrants across both roots are DEMONSTRATIVE and all
carry a `fail` verdict; there is not one argumentative warrant in either
run. Final labels: P-R1 435 accepted / 104 refuted; P-C1 909 accepted /
163 refuted / 4 suspended-unsupported.

### Is this local to these two runs?

No, and yes. The structural sweep over **all 60 committed roots that
recorded criticism** (2 639 criticism events, 3 901 critic-role artifacts)
finds that only **250 critic artifacts — 6.4% — were ever exposed to a
conjecture dispatch**, but that **35 of the 60 roots showed at least one**.
The channel is not architecturally absent. It is absent in these two runs,
which are the two newest and largest, while July and early-August roots
(`live_tri_2026-07-27`, `corpus-enrichment-patrol-pilot`, `live-two-seat-ab-
s6`, `rung5-dumb-alternative-backend`) routinely fed criticism back. Across
the whole tree, warrants are **1 215 demonstrative to 32 argumentative**:
prose criticism almost never mints one anywhere.

---

## 2026-08-26 — segment 2: the residue

*Accepted does not mean true, and measured does not mean explained.* What
this tranche did NOT establish:

1. **R2 (prose-quote) has no discriminating power and must not be quoted as
   a rate.** Its placebo is 98–100% in both roots: a quoted span almost never
   survives into ANY other candidate, criticism or no criticism. The
   instrument cannot detect coupling even where coupling exists. Its
   `CouplingRate` of 98–100% is an artifact of batch generation, not a
   finding, and only its placebo-corrected value (−1.9 pp, +0.0 pp) is
   admissible — as "no signal", not as "no effect".
2. **R1 measures conformance, not responsiveness.** The "criticized respect"
   under R1 is the problem's own admission criterion, so R1 answers "did the
   next candidate satisfy the admission test the last one failed". That is
   the sharpest respect the record types, but it is not the same question as
   "did the conjecturer respond to the criticism".
3. **The channel census is about the context pack only.** It proves no
   criticism entered a conjecture dispatch's prompt
   (`workflow-context-exposure-v2`). It does NOT exclude indirect influence
   through scheduler ranking, attention, spawn pressure or budget. Those
   channels are unmeasured here, and a zero on one channel is not a zero on
   all of them.
4. **The dispatch→artifact link is a content match, not the record's own
   pointer.** `workflow-semantic-admission-v1.admitted_refs` resolve to
   nothing on disk (0 of 163 in P-R1), so criticism cases are matched to
   their registered artifacts on a 120-character normalized prefix: 86 of 89
   in P-R1, 110 of 111 in P-C1. The 3 and 1 that did not match are reported
   as `unlocatable-in-log`, never silently dropped. Parked as **P1**.
5. **Quote matching is conservative but still a judgement.** Spans are
   compared whitespace- and edge-punctuation-insensitively, elided `A … B`
   quotations count as accurate, and only spans ≥30 characters are counted.
   A critic that paraphrases without quotation marks is invisible to this
   instrument in both directions.
6. **Cycle alignment is approximate.** Log seqs are mapped to cycles by
   cumulative token spend against `progress.jsonl`; that puts P-C1's last
   improvement near cycle 6 of 15, while that tranche's own RESULTS.md
   records the best score as reached "by cycle 10". Both are consistent with
   "frozen long before the end"; neither is re-derived by the other, and this
   census's claim is stated in log seqs, which are exact.
7. **Two roots carry the Q5 rates.** The other 58 have no run-owned scalar
   measure, so CouplingRate/RepairRate/NeglectRate are simply not defined
   there. The sweep answers only the structural question for them.
8. **Declines are uncounted for correctness.** 17 of 112 and 56 of 175
   dispatches replied `attack: false`. Whether those targets deserved to
   survive is not measured — it would need a verdict this census has no
   mechanical basis for.
9. **This tranche cannot say whether a live channel would have helped.** The
   35 roots that did feed criticism back have no scalar score either. That
   the two exposed roots also failed to improve is consistent with both "the
   channel would not have helped" and "the channel was never given a run with
   a scoreboard". Answering it needs a live A/B, not a census. Parked as
   **P2**.
10. **W1 overlap unresolved.** W1's root inventory was not on `origin/main`
    when this tranche started, so `roots.py`/`roots.json` derive an
    independent list of 60 roots. The synthesis round should diff the two
    rather than assume they agree.

---

## What this does NOT mean

It does not mean the harness's refutations are wrong: 463 of 463 re-derive
correct, and the commitment each names is in its target's interface every
time. It does not mean the critic models are bad: their attacks name
premises, offer counterexamples and quote their targets accurately about
three times in four, and 73 dispatches across the two runs declined to
attack rather than manufacture a fault. What it means is narrower and more
fixable: **the criticism those models produced was recorded and then not
routed anywhere it could act**, and the thing that did act under the name of
criticism was the problem's own admission test.

## Instruments (all committed, all re-runnable)

    python roots.py roots.json                              # the root inventory
    python census.py <root> <out.json>                      # per-criticism record
    python q5.py <root> <census.json> <out.json> [--checker <dir>]
    python sweep.py roots.json sweep.json                   # all 60 roots
    python tables.py  > TABLES.md
    python exemplars.py > EXEMPLARS.md

Gate for a read-only tranche: `git diff --stat origin/main` names no path
under `src/` or `tests/`.

---

## 2026-08-26 — segment 3: the gate

    $ git diff --stat origin/main
     17 files changed, 40201 insertions(+)     # all under
                                               # experiments/2026-08-26-run-anatomy-w2-criticism/
    $ git diff --name-only origin/main | grep -E '^(src|tests)/'
    (no output)                                # GATE PASS

    $ git status --short experiments/2026-08-25-poietics-program \
                         experiments/2026-08-25-change-constructive-frontier
    (no output)                                # no committed root modified

Every root was opened `read_only=True`. `tables.py` re-run from the
committed JSONs reproduces `TABLES.md` byte-for-byte.
