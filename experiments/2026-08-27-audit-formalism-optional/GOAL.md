# GOAL — the formalism-optional audit

Tranche dir: `experiments/2026-08-27-audit-formalism-optional/`
Route: `deepreason-orchestrator` (measurement tranche; READ-ONLY on `src/` and `tests/`).
Opened: 2026-08-27. Branch: `claude/formalism-optional-audit-mfdpdo`.

## The question, in one line

Is prose PENALISED anywhere — in code or in the committed record — relative to
formal conjectures and criticism?

## Authority (verbatim, both texts)

**(1) The standing law** — CLAUDE.md, §Operator design laws, 2026-08-08:

> **Formalism is an option, never an obligation** (2026-08-08, repeated by the
> operator "endlessly" — do not make them repeat it again): nothing may force a
> conjecture to be formal, and nothing may penalize a conjecture for being
> informal — not admission, not rank, not criticism exposure, not acceptance.
> Formal backing may grant protection (prose-immunity); its absence grants no
> disadvantage. Any design that weights outcomes on conjecture KIND violates
> this law. See DUAL_MODE_CONJECTURE_PREPLAN.md R-g for the full binding form.

**(2) The commissioning words** — the operator, 2026-08-27:

> "prose seems to have taken a back seat. So next task. Figure out whether prose
> is penalised anywhere over formal conjectures and criticism."

## The motivating incident (the audit's opening case)

`experiments/2026-08-27-pc2b-symmetric-reasoning/RESULTS.md`, "Two populations,
and the gap between them is a finding":

- Artifact level (the run's own scored candidates): 4 candidates, 0 valid, all
  four `CLAIM_INFLATED`.
- Blob level (W1's mechanism census over what the model actually WROTE): 6
  constructions, 1 VALID at 0.0127781713, claiming 0.01276 — an honest claim.

> "**The harness wrote a good, honestly-claimed construction and never scored
> it.**"

Whether that drop-out is a PROSE PENALTY AT ADMISSION is the first thing this
audit walks, line by line.

## Falsifiable success criterion

The tranche succeeds if it delivers, from evidence and not from reading
impressions:

1. **A complete site table** — every site in `src/` where a conjecture's or a
   criticism's KIND (formal vs informal; battery-carrying vs not; envelope vs
   prose; machine-evaluable claim vs argument) influences any outcome, each row
   classified LAWFUL-PROTECTION / UNLAWFUL-PENALTY / STRUCTURAL-GAP / NEUTRAL,
   with the sweep terms listed so a reader can re-run the sweep. NO SAMPLING.
2. **Kind-outcome tables over the committed record** — artifacts classified by
   kind with the operationalization stated, compared on admission, acceptance,
   criticism exposure, refutation, survival, reach eligibility, render presence,
   quoting counts.
3. **A verdict on each of the law's four named outcomes** — admission, rank,
   criticism exposure, acceptance — each CLEAN, PENALIZED (naming the site), or
   GAP.
4. **One parked fix prompt per UNLAWFUL-PENALTY row**, ready to paste.

The tranche FAILS if any of the four is delivered by sampling, by assertion, or
by code-reading unsupported by a runnable check.

## Scope contract

- **READ-ONLY on `src/` and `tests/`.** `git diff --stat origin/main` must show
  no file under either. Findings become PARKED prompts, never fixes.
- No pytest gate is owed (no code changes). `docs_verify` only if a map document
  moves — it should not.
- Anything noticed that is not a kind-penalty question goes to `PARKED.md`.

## Map preflight — resolved ids

Read before designing, in this order:

| id | why it is in scope |
|---|---|
| `DR-INV-frozen-surfaces` | read first, always (read-only tranche: no contact expected) |
| `DR-CON-conjecture-kinds` | **the covering document** — formal vs informal, where kind is signalled, and the R-g guardrail |
| `DR-CON-criticism-source` | `crit.py` — the two supremacy guards, and which one decides a STATUS |
| `DR-CON-conjecture-source` | `rules/conj.py` — the socket that proposes candidate artifacts (the admission path) |
| `DR-CON-scheduler-ranking` | `Scheduler._select_problem` — rank |
| `DR-CON-warrants-and-attacks` | no warrant, no edge, no REFUTED |
| `DR-CON-packs-and-token-economy` | render allocation — whose content reaches packs |
| `DR-CON-discharge-channel` | the F1 discharge screen |
| `DR-CON-proof-debt-and-localization` | derived-judgment backing |
| `DR-SUB-evaluation` | "where formal meets informal" — programs, oracles, measures, informal trials |
| `DR-SUB-rules` | conjecture, criticism, warrants, spawn, guards |
| `DR-SUB-scheduler` | selection, cycles, budgets, allocation |
| `DR-SUB-llm` | packs, contracts, wire firewall (the admission funnel) |
| `DR-SUB-adjudication` | warrants → attack edges → status labels |
| `DR-SUB-calculus` | Rung 5 promotion criteria (demarcation, observation-valued) |
| `DR-SUB-scratch` | authoring, render receipts, attention |
| `DR-SEAM-evaluation-x-rules` | read BEFORE either side — the formal/informal meeting point |
| `DR-SEAM-llm-x-rules` | wire contract → candidate |
| `DR-SEAM-scheduler-x-rules` | rank and dispatch |
| `DR-SEAM-adjudication-x-rules` | warrants → labels |
| `DR-SEAM-calculus-x-rules` | promotion |
| `DR-SEAM-capabilities-x-rules` | capability proposals as an executable-commitment path |

Prior art this tranche must reuse rather than rewrite:
`experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md` (the D1 census that
produced `DR-CON-conjecture-kinds`), the W1 form census
(`experiments/2026-08-26-run-anatomy-program/W1-form-census/`), W2's criticism
census and W3's evidence/scratch tables, and
`experiments/2026-08-26-run-anatomy-program/ROOT_INVENTORY.json` (54 roots).

## Outcome classes walked (the checklist, from the law plus machinery since)

admission (walked FIRST — the P-C2b dropped construction, line by line) · rank
and scheduling (hv-floor, attention, wound counts) · criticism exposure and
routing · acceptance/adjudication · reach eligibility (the P1-reach fix's
classification) · promotion criteria (Rung 5 demarcation, observation-valued) ·
the knowledge view's `active` conjunct · render allocation · the F1 discharge
screen · budget and allocation.

## Deliverables

`SITES.md` (the site table), `TABLES.md` (kind-outcome tables), `EXEMPLARS.md`
(verbatim exemplars, the P-C2b construction traced end to end), `VERDICT.md`
(four named outcomes), `PARKED.md` (one fix prompt per UNLAWFUL-PENALTY),
`RESULTS.md` (honest ledger, residue stated).
