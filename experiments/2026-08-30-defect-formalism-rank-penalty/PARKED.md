# PARKED — what this lane did not do, and the prompts to start each one

Every entry is a ready-to-send prompt: starting the follow-up should cost a
paste, not an authoring session.

---

## L1 — the P2 fork itself (the reason STOP.md exists)

**What.** The three roads for the coverage axis are priced, the law narrows
them to one, and road (a) is BUILT AND PARKED on `claude/b2-lane-C` — but the
choice is the operator's, and it has not been made. See `STOP.md`, which is
answerable with one word. Nothing here is blocked on anything except that word.

Not restated as a prompt: `STOP.md` **is** the prompt.

---

## L2 — SITE (b) = P3, the prose-criticism penalty. NOT TOUCHED, BY ITS OWN BRIEF

**What, carried forward verbatim from
`experiments/2026-08-27-audit-formalism-optional/PARKED.md:119-129`:**

> **What.** A DEMONSTRATIVE warrant changes a status under every mode. An
> ARGUMENTATIVE one requires `ADJUDICATION_STATUS_AUTHORITY_ENABLED` (default
> `False`) plus a non-`observe_only` `ARGUMENTATIVE_AUTHORITY` (default
> `observe_only`) plus a cross-family judge ensemble that survives referential-
> integrity, unanimity and paraphrase screens. Measured across 6 789 committed
> artifacts: **8 argumentative warrants against 551 demonstrative.**
>
> This is a penalty on prose CRITICISM. The standing law speaks of conjectures;
> the 2026-08-27 commissioning words explicitly name criticism too. It is parked
> rather than filed as a violation because the asymmetry has a stated ground and
> because the operator's own 2026-08-09 law is wary of judges.

**Why this lane did not implement it.** Its own brief forbids designing before
the operator answers, in its own words (`PARKED.md:132-136`): "Route through
dr-ask-the-right-question FIRST" and "THE QUESTION FOR THE OPERATOR (do not
design before it is answered)". The heading itself files it as "an operator
decision, not a defect" (`PARKED.md:117`). This lane read
`src/deepreason/config.py:504-509` and `src/deepreason/informal/trial.py:963`
and wrote to neither.

**One correction the next runner must not re-derive.** The line numbers in the
2026-08-27 brief have rotted. `SITES.md:50` and `PARKED.md:151` cite
`src/deepreason/informal/trial.py:920` for `formally_backed(target)`; today
that call is at **`trial.py:963`**. `config.py:504-509` is still exact. Verify
before quoting.

```
Route through dr-ask-the-right-question FIRST, then dr-change-orchestrator only
if the operator wants a change.

THE QUESTION FOR THE OPERATOR (do not design before it is answered), carried
forward verbatim from experiments/2026-08-27-audit-formalism-optional/
PARKED.md:135-141:

  A formal refutation always changes a status. A prose refutation changes none
  unless you switch judges on, and you have said you would prefer to do without
  them ("they prosecute without any discernable discrimination", 2026-08-09).
  Measured over every committed root: 8 prose warrants, 551 formal ones.
  Is that the price you intend prose criticism to pay, or do you want a
  judge-free road by which an argument alone can change a status?

ONE THING THE QUESTION'S OWN AUTHORITY HAS SINCE MOVED, and the next runner
must put in front of the operator with it: the 2026-08-09 judge caution quoted
inside that question was AMENDED by the operator on 2026-08-28 on the record's
own evidence (CLAUDE.md, "The judge law, amended on the record's own
evidence"). In the frozen configuration judges UNDER-convict -- 11.9%
sensitivity, 0-2.5% false conviction -- and it is the CRITIC's raw objection
flow, not the judge gate, that is indiscriminate. The question as written
still quotes the superseded caution. Put the amendment beside it so the
operator answers against what the record now shows.

If the answer is "I want a judge-free road", the design constraints are already
ledgered and must be read first:
  experiments/2026-08-14-change-calculus-reconciliation-v2/RECONCILIATION.md
    -- the siren example, R26/R27: X must fall BY ARGUMENT ALONE, and the
       design's answer was to route it through a PROGRAM (the premise rent
       battery) rather than to let prose mint a warrant directly. That is the
       precedent to either extend or overturn.
  CLAUDE.md, the 2026-08-09 solo-run law: any road must work for a solo model.
  src/deepreason/informal/trial.py:963 (NOT :920 -- the brief's line has
    rotted) and the guards around it.
  src/deepreason/config.py:504-509 (still exact).

Also read, because it now binds this question directly: CLAUDE.md's 2026-08-28
ungated-seats law -- "Gates are always optional: with warnings" -- which says
these two switches must be turnable on per run and that switching one emits a
typed WARNING, never a refusal and never silence. Whatever road is chosen, the
switches themselves are already required to be reachable by configuration.

Evidence: experiments/2026-08-27-audit-formalism-optional/VERDICT.md section 4;
TABLES.md (warrant rows); KIND_CENSUS.json.

END STATE if a change is wanted: a specified road, its solo-compatibility
argued explicitly, and its determinism story stated (what replays byte-for-byte
when the decisive input is an argument).
```

---

## L3 — the `hv` and `reach` axes share the coverage axis's shape

**What.** `reach` skips an artifact with no evaluable commitment outright
(`src/deepreason/measures/reach.py:128-132`, `if not carried: continue`) and
`hv` leaves a non-carrier at its 0.0 default. Both then enter the same
maximising `frontier()` as the coverage axis does. In the two roots measured
today, `hv` and `reach` are 0.0 for **every** survivor of both kinds, so no
penalty is measurable there — but a run in which a formally-backed artifact
earns `hv > 0` reproduces exactly the same domination on a different number.

The 2026-08-27 audit rowed these STRUCTURAL-GAP, not unlawful, so they are
correctly out of this lane's cone. Recorded here so nobody reads the coverage
repair as having closed the class.

```
Route through dr-audit-orchestrator (a scoped read-only follow-up), or park
until a run produces a survivor with hv > 0.

GOAL: decide whether `hv` and `reach` carry the same unlawful shape the
coverage axis carries, by MEASUREMENT rather than by analogy -- find or
generate one root with a commitment-free survivor and a formally-backed one
with hv > 0, and read whether the commitment-free one leaves the frontier.

Do this only AFTER the P2 fork is answered: if road (a) is chosen, the same
NOT-MEASURED rule may already cover hv and reach, because road (a)'s
dominance rule excludes any axis absent from either point -- but hv and reach
today emit 0.0 rather than omitting the key, so the rule would not fire. That
is the specific thing to check first, and it is a one-line question:
does `run_report` emit `hv`/`reach` keys for an artifact that was never
sampled or never reached?

Evidence: experiments/2026-08-27-audit-formalism-optional/SITES.md rows for
measures/reach.py:137 and scheduler.py:1330. Cite those two sites by SYMBOL,
not by line: the audit's own line numbers had already rotted when this bullet
was written, and this bullet's first correction of them rotted again inside
this same lane. `grep -n "if not carried:" src/deepreason/measures/reach.py`
and `grep -n "if is_hv_floor(kappa):" src/deepreason/scheduler/scheduler.py`
find them on any tree (:131 and :1357 on this one); experiments/2026-08-30-defect-formalism-rank-penalty/
proof/footprint_2026-08-30.txt shows hv and reach at 0.0 for all 291
survivors across both roots measured.

END STATE: a row saying MEASURABLE or NOT-MEASURABLE with the root that
settles it. No code changes in the audit itself.
```

---

## L4 — `docs_verify` was not run by this lane

**What.** The batch's load rule forbids running `tools/docs_verify.py` inside a
lane (four lanes share a 4-CPU box; a measurement taken under load is not a
measurement). Each map `check:` this lane added or changed was run
INDIVIDUALLY by hand and its output recorded in `DELIVERY.md`. The full
`docs_verify`, `--audit` and `--links` passes are owed at the batch's fan-in,
not here.

Note for fan-in, from `RECON-SHARED.md:7`: `docs_verify --audit` already
reports at least one pre-existing finding (`SEAM-llm-x-rules.md:54`
unparseable), so "--audit reports 0 findings" is not achievable until lane D
repairs it — do not attribute that finding to this lane.

---

## L5 — no `Config` field was added, deliberately

**What.** `src/deepreason/config.py` is the one file this lane could have
collided with lane B on (lane B's P9 flag lands there too). Road (a) is a
semantics repair to an existing axis, not a new customization point, so it
needs no knob and this lane wrote nothing to `config.py`. Recorded so a later
reader does not assume a knob was forgotten.

If the operator wants the road SELECTABLE per run rather than fixed — which
the 2026-08-26 modularity law would support — that is a separate, larger
change and belongs in its own tranche, with the axis-scoring rule becoming a
registered, versioned policy rather than a literal.
