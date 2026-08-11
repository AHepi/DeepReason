# Decision sheet — Items 4+5 (per-role qualification, error catalog, intake tool)

DESIGN-AND-STOP. SPEC.md is committed; no code has been written. Two
questions need the operator's own words before any implementation
starts.

## Question 1 — how far does "per role" go?

Your words: "The per role qualification needs to be per role with
added error messages."

Today, a run with multiple models bound to different roles (seats)
already reports readiness PER ROLE (Rung S3's `get_seat_readiness`) and
already runs a qualification battery — the ~14-minute, ~1,160-call test
suite that certifies a model can fill each role before a real run is
allowed to use it — per DISTINCT model as well as for the whole
combination together. What's still missing is only the READABLE
MESSAGE when one of those checks fails.

There are two ways to read your sentence:

- **(a) Add readable messages only** — leave today's qualification
  mechanics exactly as they are, just make the failure text plain
  English. Small, safe, ships fast.
- **(b) Change what "qualified" means** — let models that were each
  separately certified before mix together WITHOUT re-running the full
  battery for the new combination (today, every new combination of
  models pays its own full ~14-minute battery even if every model in it
  was already certified alone). This would cut real cost for you if you
  swap models between roles often, but it touches one of the five parts
  of the code we've locked down as too risky to change without your
  explicit go-ahead each time (the "frozen surfaces" — this one is the
  code that decides whether a certification still counts).

**Recommendation: (a).** Your sentence reads as a complaint about
unreadable messages, not about paying for redundant certification —
and (a) ships the readability fix now, while (b) stays fully designed
and ready to build the moment you want it (it's already written up in
a parked file from a prior tranche).

## Question 2 — who gets the new intake tool by default?

Your words: "The form you showed is very convoluted... I'm thinking a
tool should be the default for small models... The form also needs to
be simple enough for a coding human to fill out."

We're replacing the convoluted prose form with a validated FILE (a
schema-checked config, like filling out a structured form a computer
can check for you before you spend any money on API calls) plus one
command that checks it and tells you in plain English what's wrong, if
anything. That part isn't in question.

What's in question is scope: your words say "default for small
models." A separate piece of research we ran this session argues it
should be the default for EVERYONE, including you at the terminal and
large models — because a checked file has no back-and-forth
conversation to get lost in, and you can fix one line and re-check it,
which neither a smaller nor a larger model loses anything by having
too.

**Recommendation: make it the default for every caller**, keeping the
old prose form only as documentation generated FROM the file's schema
(so the two can never drift apart again), not as a second way to start
a run.

## What ships once you answer

Once you answer both questions, the tranche splits into two small,
separately-delivered pieces (~420 lines total, no frozen surfaces
touched under recommendation (a)): the plain-English error catalog
(covering the ~44 qualification/doctor codes most relevant to your
complaint first, with the rest queued as named follow-ups, never
silently declared done), and the schema-checked intake tool with its
CLI command and a matching tool for model callers.

Everyday analogy: this is the difference between a paper form you might
fill out wrong and mail back and forth to find out (today), versus an
online form that circles every blank in red before you can submit it
(the tool) — with a printed copy of that same online form, generated
automatically, kept for anyone who'd rather read it on paper (the
regenerated FORM DR-1).
