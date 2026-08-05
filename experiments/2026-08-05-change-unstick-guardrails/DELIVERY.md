# Delivered: unstick guardrails (reduce operator steering)

Six skill files changed; ~55 lines.

| R | Disposition | Where |
|---|---|---|
| R1 park-with-prompt | done | deepreason-orchestrator scope item 1; dr-change-orchestrator scope item 2; dr-deliver-change step 3 + template ("recommended next:" line) |
| R2 resumability | done | dr-plan-steps CHECKLIST header State: line; dr-execute-step step 6 refresh rule; dr-drive-harness §1 one-line resume protocol |
| R3 stop-with-recommendation | done | dr-execute-step step 4 (two-failure stop format); dr-change-orchestrator stop conditions; dr-drive-harness calibration paragraph |
| R4 process hygiene | done | dr-drive-harness new §5b, four rules each citing its paid-for incident (pkill self-kills ×2; concurrent-instrument corruption ×3 measurements) |
| C1 jargon layer excluded | honoured | no prose-translation content; operator's next project |
| C2 general wording | honoured | incidents cited as evidence, not as scope |
| C3 skills only | honoured | git diff --stat: 6 skill files + tranche dir |

Acceptance: all four S-item greps pass (3/3 files "ready-to-send";
State: in both; "Resume tranche" present; recommendation in 3/3;
"Process hygiene" present). Docs-only change: no gate, sweep,
docs_verify, or smoke owed (packaging surface untouched).

Evidence base: this session's steering record — five consecutive
operator prompts (P1, smoke, S1, T2, T1) each derivable from the
executor's own parked entry; one stuck-window re-entry requiring a
hand-written prompt; two pkill self-kills; three load-corrupted gate
measurements across two tranches.

Design limit, recorded: these rules make a weaker agent stop LEGIBLY
and RESUMABLY at its ceiling; they do not raise the ceiling. The
mechanization direction for that is the parked mini-harness pre-plan
(docs/proposals/BEHAVIOR_MODES_PREPLAN.md, final section).
