# PARKED — the premise-invitation reachability tranche

Nothing here was fixed. Each entry is one line of WHAT plus a ready-to-send
prompt: the follow-up should cost the operator a paste, not an authoring
session. Numbering continues the run-problems audit's own `PARKED.md`, which
holds P10-P13; these are P14-P16. **ERRATA/park numbering may collide at merge
with the two parallel windows (render-layout, manifest) — these were minted from
the tail of `experiments/2026-08-28-audit-run-problems/PARKED.md` at
2a5e984c8, and a merge that finds P14-P16 already taken should renumber these,
not the others.**

---

## P14 — the planted-presupposition probe (NOT authorized in this window)

**What.** The audit's residue item 2: replay epoch 6 seq 180's prompt with a
deliberately malformed presupposition planted in the problem text, where a
correct seat MUST fill `premise`. It is the only experiment that separates "the
seat declines the channel" from "the seat sees nothing wrong with the question"
— a distinction `PREREG_LITE.md` said in advance the original probe could not
make. Explicitly not authorized for the P11 window; not started.

**Ready-to-send prompt:**

```
Route: a live experiment under the change family's evidence discipline
(pre-register before any call; raw preserved; model prose is never evidence).
Sequence AFTER the P11 ladder tranche is merged, so the seat is measured on the
channel as it now stands rather than as it stood when it was shut.

Goal, one sentence: separate "the critic seat declines the citation channel"
from "the critic seat sees no malformed presupposition", which no committed
measurement currently distinguishes.

Method, frozen before the credential is used: take the verbatim prompt bytes of
the one dispatch that saw the whole channel, plant a presupposition in the
problem text that forbids nothing and is plainly false, and run the same two
arms as the original probe (control, and control + a worked exemplar). ~40k
tokens. State the decision rule BEFORE running: on the planted text a correct
seat MUST fill `premise`, so a null there is evidence about the seat in a way
the original probe's null was not.

Evidence, all committed:
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md section F-B
  experiments/2026-08-28-audit-run-problems/PREREG_LITE.md
      -> what the first probe CANNOT establish, frozen before it ran
  experiments/2026-08-28-audit-run-problems/probes/live/SUMMARY.json
      -> 0/8 control, 0/8 exemplar, on the UNPLANTED text
  experiments/2026-08-28-change-premise-invitation-reachability/ANSWERS.md
      -> answer (2): the four cases, and the receipt that now types them

Do NOT read the first probe's 0/16 as "the seat will not cite". A null premise
is legal when the seat sees no malformed presupposition; that is the whole
reason this experiment exists.

End state: a pre-registered result that either shows the seat filling `premise`
on planted text (so the channel works and the earlier nulls were correct
answers) or shows it not filling it (so the prompt surface is the next thing to
work on), recorded as a dated segment with its residue named.
```

---

## P15 — the batch-unanimity rule withholds the invitation on most dispatches that could carry it

**What.** Measured in this tranche and NOT one of P11's three questions, so not
fixed. Every critic dispatch in the four committed technique roots is a batch
(`contract_id: batch-critic.v2`), and `_batch_premise_invitation`
(`rules/crit.py:1631`) withholds the invitation unless every target in the batch
answers ONE problem. On the epoch-5 root a problem stood an invitation at **9 of
10** dispatches and only **3** packs carried it; that root's targets split
across two problems (28 addressed to the seed question, 6 to
`conn:0a89b2b812ae`). So the ladder P11 delivered raises the number of dispatches
at which the channel COULD open, and this rule still decides how many actually
see it.

**Ready-to-send prompt:**

```
Route: dr-change-orchestrator (a design change -- the rule is deliberate and
documented, it is simply narrower than anyone measured). Sequence AFTER the P11
ladder tranche, whose measurement this is.

Goal, one sentence: let a batched criticism dispatch carry the premise
invitation for the problem its targets actually share, instead of withholding it
whenever any batch-mate belongs to a different problem.

Evidence, all committed:
  experiments/2026-08-28-change-premise-invitation-reachability/SPEC.md M6
      -> epoch 5: 9 of 10 dispatches had an open problem, 3 packs carried it
  experiments/2026-08-28-change-premise-invitation-reachability/probes/p11_ladder_counterfactual.py
      -> re-runnable per-dispatch replay; add the per-target join this park needs
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md section F-B

Code:
  src/deepreason/rules/crit.py:1631 _batch_premise_invitation -- "One invitation
      for a batch, and only when the batch is unanimous"
  src/deepreason/rules/crit.py:1268 _premise_invited_problem -- the per-target
      lookup the batch rule collapses

Read DR-CON-criticism-source and DR-SEAM-scheduler-x-rules before designing, and
DR-INV-frozen-surfaces first.

The existing rule has a real reason -- "no single problem is the subject of the
question and the invitation is withheld rather than guessed" -- so the design
question is not "remove it" but "what does a MAJORITY batch legitimately ask
about". Price the pack cost the way P11 did (the invitation paragraph and the
citable legend are ~4139 characters together, measured from the prompt bytes),
and check `docs/map/SEAM-rules-x-scratch.md`'s pinned parameter lists for
render_crit_pack/render_batch_crit_pack before assuming a new pack argument is
available.

End state: a stated rule for which problem a mixed batch may be invited about;
the per-target counterfactual re-run showing the new shown/open ratio; full gate
0 failed; map moved in the same commit.
```

---

## P16 — `PREMISE_INVITE_AFTER` is not reachable as configuration, and the modularity law says it should be

**What.** The operator's 2026-08-26 law: "every behavior a run can vary is
reachable as CONFIGURATION or a REGISTERED, VERSIONED ARTIFACT — never by
editing code." The invitation threshold — and now the ladder's step size, which
is the same constant — is a module constant. `premises.py:68` records exactly
why: a new top-level `Config` field needs a line in `run_manifest.py`'s
`_versioned_source_config_data`, which is frozen surface 4, and the P11 window's
frozen-surface rule made that a STOP. So the tension is recorded rather than
resolved, and it is a real one: today an operator who wants a different
invitation cadence has to edit code, which is the thing the law forbids.

**Ready-to-send prompt:**

```
Route: dr-change-orchestrator. FROZEN SURFACE FORECAST: CONTACT EXPECTED --
run_manifest.py's _versioned_source_config_data is frozen surface 4. Request the
grant in SPEC.md BEFORE any code, per the discipline; the monitor reviews it
there. Do not start implementation without it.

Goal, one sentence: make the premise invitation's cadence reachable as
configuration rather than by editing premises.py, without minting a Config field
that moves a qualification subject digest.

Evidence, all committed:
  src/deepreason/premises.py:68        the constant, and its recorded reason
  src/deepreason/premises.py:625       premise_work_invited -- the ladder that
                                       uses it as its step size
  CLAUDE.md, the 2026-08-26 modularity law, operator verbatim
  experiments/2026-08-28-change-premise-invitation-reachability/SPEC.md A4
      -> the assumption this tranche recorded instead of resolving

Worth checking FIRST, before designing a Config field: whether the signal
contract's own VERSIONED layer (DR-INV-signal-contract, DR-REC-revise-
allocation-policy) is the right home for this, since it exists precisely to let
a policy value move as a recorded artifact rather than as a code edit. If it is,
the frozen surface may not need to be touched at all -- which would make this a
much smaller tranche than it looks.

End state: the cadence set from configuration or from a versioned registered
artifact; an architecture check that goes red if using it requires a code edit
(the modularity law's "enforced" half); full gate 0 failed; map moved in the
same commit.
```
