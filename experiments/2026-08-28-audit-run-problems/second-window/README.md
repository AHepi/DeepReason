# Second audit window — same prompt, independent run

The operator ran the run-problems audit prompt in two windows. The window on
branch `claude/audit-pt1-technique-run-p6nh6v` (probe-backed, live-probe
registered, based on main 29e33f702) is the CANONICAL report one directory up.
This directory preserves the other window's full report
(branch `claude/audit-pt1-technique-run-wo5y5i`, based on cae5df984,
offline-only), relocated at merge by the monitor to avoid a path collision.

The two reports AGREE on every shared finding. Unique to this window, and
worth reading alongside the canonical report:
- The 19 capability heartbeat cycles of epoch 6 characterized as BUDGET-DENIED
  NO-OPS on one dead package (sharpens canonical F-F).
- One budget-denial condition shown to have at least FOUR distinct
  dispositions, not two (extends canonical F-E / P2).
- The anti-E28 receipt `premise.work-invited.v1` reports 0 on a run where the
  mechanism fired and completed — an instrument defect the canonical report
  does not carry (see this window's finding #10).
Where the two differ in depth (P8: here UNDETERMINED, canonical REFUTED the
stochastic reading), the canonical report governs.
