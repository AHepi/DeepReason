# Request: reduce operator steering — parked queues, resumability, legible stops, process hygiene

Captured 2026-08-05, monitor session.

## Operator's words (verbatim)

> Ok so I need you to think through something. During this
> conversation, you have had to constantly steer the orchestrator. Some
> of it is because it needed my feedback. Some of it is because it
> couldn't solve a problem. Can you think of any way of improving the
> workflow so that less capable agents don't get stuck so easily? Its
> essential to get this right. Also, I need a layer that converts all
> the AI output jargon into human readable prose, whether it's a human
> communicating to an AI to automate upgrades or a user on the other
> end of MCP trying to get info about how to achieve certain results.
> This part I want to work on next. But for now, workflow updates

Monitor proposed four changes (park-with-prompt; resumability contract;
stop-with-recommendation; process-hygiene traps), grounded in this
session's steering record.

> Do it!

## Requirements

- R1 (park-with-prompt): every PARKED entry is written for its future
  runner at park time — one line of WHAT plus a ready-to-send prompt
  (route, one-goal statement, evidence pointers, end state). Tranche
  closes list the open queue and recommend a next item.
- R2 (resumability): a tranche is continuable by a fresh session from
  its committed artifacts alone; CHECKLIST.md carries a live State:
  line refreshed at every commit; the fresh-window prompt is one line.
- R3 (stop-with-recommendation): every stop presented to the operator
  leads with the decision needed in one sentence, the options priced,
  and a recommendation with its reason.
- R4 (process hygiene): the driving manual carries the
  paid-for-in-the-record operational traps — kill by PID, never run
  the gate concurrently with docs_verify, measure on an idle box,
  launch long work detached.

## Constraints

- C1: the jargon-to-prose layer is the operator's NEXT project — out
  of this tranche entirely.
- C2: general-use wording (standing rule).
- C3: skill files only; no src/, tests/, or map change.
