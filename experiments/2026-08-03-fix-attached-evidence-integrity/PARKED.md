# Parked — noticed during this tranche, deliberately not done

One line each. Parking is a decision, not a deferral of judgement: each of
these was looked at, scoped, and excluded from THIS goal.

- Ladder audits print `replay_valid: null` because `verify_root` returns
  `{stats, violations}` with no `valid` key; validity is `violations == []`.
  Visible in this tranche's own `triage-audit.json`. Handover item 4, own commit.
- Ladder audits count v6 scratch via `scratch*` log measures, but v6 scratch
  rides OBJECT records (`objects/scratch-*`); `triage-audit.json` accordingly
  reports `scratch_events: 0`. Handover item 4, own commit.
- `INV-frozen-surfaces.md` surface 4 prose says the sweep census is 11 where
  `DR-SEAM-harness-x-verification`'s Traps says 14 raise by direct manifest
  load and 3 predate manifests. Two instruments, two true numbers; the SEAM doc
  already flags the disagreement. Handover item 2 — a diagnosis of its own.
- 14 seam documents lack `Sweep:` headers (handover, open decisions). Ratchet:
  added when each is next touched, not swept for here. This tranche touched
  `SEAM-harness-x-verification` (Traps entry) and recorded the sanctioned
  stated-reason instead of a header: that seam's agreement is the replay
  relation, enforced by whole-state comparisons (`model_dump_json`, digest
  pairs) that the FIELD && OTHER_SIDE detector cannot see; a spec targeting
  the state-comparison sites specifically remains to be designed.
