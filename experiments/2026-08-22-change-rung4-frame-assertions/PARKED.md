# Parked — found while working Rung 4, deliberately not done here

## P1 — rename `Config.RECRIT_STANDING` / `scheduler._standing_recrit_pool`

**What.** `docs/map/CON-standing-and-background.md` parks this rename "to Rung
4, where the collision becomes real". The collision IS now real — this rung
gives "standing" its calculus meaning (frame role) while the scheduler's two
names mean "still standing" (a survivor not yet re-criticised). Rung 4
disambiguates in the map (SPEC.md A4) and does not rename, because the document
itself calls the rename "a compatibility decision rather than vocabulary work":
`RECRIT_STANDING` is a `Config` field readable from profile YAML, pinned by a
check in `DR-SUB-scheduler`.

**Ready-to-send prompt:**

```
Change tranche: retire the "standing" name collision in the scheduler.
Route through dr-change-orchestrator.

AUTHORITY: docs/map/CON-standing-and-background.md's Traps section, third
row ("The word 'standing' was already taken, three times"), and
experiments/2026-08-22-change-rung4-frame-assertions/PARKED.md P1. Rung 4
gave "standing" its calculus meaning (an artifact's frame role, Def 9.3);
Config.RECRIT_STANDING and scheduler._standing_recrit_pool still mean
"still standing" — a survivor not yet re-criticised. Two senses, one word,
in one codebase.

WORK: decide and implement ONE of — (a) rename the internal symbol
_standing_recrit_pool only, leaving the Config field alone; (b) rename
both, with a Config alias so existing profile YAML keeps working; (c)
leave both and document the collision permanently. Price each in SPEC.md
before choosing. The Config field is readable from profile YAML, so (b)
is a compatibility decision, not vocabulary work.

GATE: full gate 0 failed; docs_verify full (three map checks pin these
names: DR-SUB-scheduler, DR-CON-standing-and-background, and the
RECRIT_STANDING row). Map moves in the same commit.
END STATE: one word, one meaning, or a document saying why not.
```

## P2 — inherited from Rung 3b: gate `premises.py::standing_attributions` on separation

**What.** Rung 3b's PARKED.md P1. Rung 4 wires `consultability` for FRAME
ASSERTIONS, which is what Rung 3b said it would do. Whether the premise
channel's own consultation predicate should also run the separation check is
still open and carries its own measurement obligation. Untouched here.

**Ready-to-send prompt:** see
`experiments/2026-08-21-change-rung3b-frame-separation/PARKED.md` P1 —
unchanged and still current.
