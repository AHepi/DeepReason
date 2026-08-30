# RUNTIME — what the integrity gate costs, measured rather than asserted

SPEC.md's P-FIX-4 predicted "tens of seconds, not minutes" of added gate time
from one `verify_root` per `prepare_continuation` and one per `amend`. That
prediction is RECORDED HERE AS WRONG, with the measurement that refutes it,
because a wrong prediction quietly dropped is how a cost becomes a surprise.

Box condition: this container is shared with four other lanes of the same
batch, running their own suites. `python -m pytest` was single-process
(`-p no:randomly`, no `-n`). Wall clock here is therefore an UPPER bound and
CPU time is the fairer figure; both are given.

(figures filled in below from the two ring runs)
