# REQUEST — Rung 1: vocabulary and groundwork

Route: `dr-change-orchestrator`. **Rung 1 of the v2 calculus program**
(`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`). One rung,
one tranche.

Date: 2026-08-14. Branch: `claude/calculus-reconciliation-v2-qqghvn`.

## 1. Authority

The operator's word, verbatim, on the delivered v2 design-and-stop tranche:

> go ahead

Delivered immediately after that tranche's closing report, which stated:
"Rungs 1 and 1b are now unblocked and can start immediately", and after the
operator answered D-2 (Road B) and D-7 (option iii). The substantive authority
is therefore the v2 tranche's committed artifacts, which the operator has now
released for execution:

- **H3** (operator, pre-decided): calculus status vocabulary adopted at VIEW and
  presentation layers only; stored record labels never change; readers stay
  byte-compatible with every committed root.
- **LADDER.md Rung 1**: the H3 rendering map; the new map concept document
  `CON-standing-and-background.md`; the vocabulary hazard noted for this rung.
- **REQUEST.md Amendment 2 clause (6)** of the v2 tranche: the signal-contract
  layering is ledgered as a **CLAUDE.md design law** in this rung (the mechanism
  and its INV document belong to Rung 1b).

**One rung per tranche** (`dr-drive-harness` §6): Rung 1b is NOT started here,
however small it looks.

## 2. Requirements

| # | Requirement | Source |
|---|---|---|
| R1 | Apply the H3 mapping at the display layer: `accepted` renders as `unrefuted`. | H3, LADDER Rung 1 |
| R2 | **Stored labels never change.** `Status.ACCEPTED.value` stays `"accepted"`; no event payload, object, or machine-JSON key moves. | H3 (binding) |
| R3 | Every committed root replays byte-unchanged; `root_sweep` shows zero verdict drift. | LADDER, program-wide |
| R4 | Human-facing renderers route through the display seam rather than printing the stored value directly. | LADDER Rung 1 |
| R5 | Mint `docs/map/CON-standing-and-background.md` (`DR-CON-standing-and-background`) carrying Prop 9.1 (the rigidity dilemma) as its rationale, with checks that can fail. | LADDER Rung 1 |
| R6 | Resolve the vocabulary hazard the v2 tranche recorded: `controller.py::_under_standing_attack` uses "standing" for *under unresolved attack*, colliding with the calculus's *frame role*. | RECONCILIATION §2L |
| R7 | Ledger the signal-contract layering (FROZEN / VERSIONED / FREE) as a CLAUDE.md operator design law. | v2 Amendment 2 clause (6) |
| R8 | No new skill or workflow (the operator's two-recorded-failures tripwire). | v2 Amendment 2 clause (6) |
| R9 | The map moves in the SAME commit as the code. | `SCHEMA.md`, CLAUDE.md |

## 3. Map preflight

Inherited from the v2 tranche's preflight and narrowed to this rung:

- `DR-INV-frozen-surfaces` — read first. **Forecast: zero contact on all five
  surfaces.** This rung changes renderers and documentation only.
- `DR-CON-authority` — owns the two authority vocabularies; the display seam is
  presentation, never authority.
- `DR-SUB-scheduler`, `DR-SUB-application` — consume `display_status_counts`.
- **New:** `DR-CON-standing-and-background` (R5), minted by this rung.

## 4. Scope decision recorded at capture time

The v2 tranche predicted ONE "standing" collision (the controller's). Scoping
this rung found **three**, all predating the calculus:

| Site | What "standing" means there | Disposition |
|---|---|---|
| `status_display.py::display_status` — renders `accepted` as **`"standing"`** for the `text` workload profile | the display label for an unrefuted artifact | **fixed here** — it becomes `unrefuted`, which R1 requires anyway |
| `controller.py::_under_standing_attack` | under an unresolved attack | **renamed here** (R6) — private method, no stored string |
| `scheduler.py::_standing_recrit_pool`, `Config.RECRIT_STANDING` | the pool of still-*standing* survivors to re-criticize | **PARKED** — `RECRIT_STANDING` is a `Config` field name pinned by a map check and readable from profile YAML; renaming it is a compatibility decision, not vocabulary groundwork. Deferred to Rung 4, which is where the calculus's standing axis actually arrives and the collision becomes real |

## 5. Amendments

(none yet)
