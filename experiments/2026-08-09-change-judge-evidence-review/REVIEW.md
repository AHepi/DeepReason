# Judge-evidence review: what do committed runs prove about LLM-judge discrimination?

**The question**, in the operator's words: what do the committed runs and
experiments actually prove about LLM-judge discrimination? The operator's
own hypothesis — "they prosecute without any discernable discrimination" —
is what this document tests, not what it assumes. Every claim below carries
its source (`path:line` or a JSON field inside a named file) so the number
can be re-derived, not just trusted.

*(Executive summary is written last, after §2-§8 are evidenced — filling it
in before the sweep would decorate a conclusion instead of testing one.)*

## Contents

- §2 Judge audit machinery and its outputs (R5a)
- §3 Trial-protocol experiments (R5b)
- §4 Adjudication-blindness fix tranche, 2026-08-01 (R5c)
- §5 Stress-triplet and lambda/experiment-module runs (R5d)
- §6 EXPERIMENT_PROGRAM_2026-07.md's judge items (R5e)
- §7 Three-way scoring: incorrect / undiscriminating / over-prosecuting
- §8 Design consequence: a judge-free or judge-minimal road for solo runs
