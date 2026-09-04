# Results — the provider reasoning wire contract

## 2026-09-04 — the alarm was about a field the harness does not send

**What was reported.** The previous tranche's probe found Ollama Cloud
refusing `"reasoning": "none"` as a bare string, and parked it with the
claim that the newest committed launch config "binds exactly that value
on its critic seat", so "any run relaunched from the newest committed
launch config would fail typed at the first seat call".

**What the record shows.** The refusal is real and reproduces exactly.
The attribution is not. The launch config binds the neutral VALUE
`"none"`; `llm/providers.py::_ollama_reasoning` spells that value
`reasoning_effort`; and no provider adapter emits a key named `reasoning`
at any value in the vocabulary. Two independent lines of evidence, one
from the record and one live:

- `run-5565bd1ef7011e3d25fef3197bdf1cdb`, whose eleven seats all bind
  `reasoning: "none"`, made 99 provider attempts with outcome
  `provider_result` and zero faults — committed 2026-09-03, the day
  before the alarm.
- A 45-call probe on 2026-09-04 accepted every body the harness itself
  built, across six models and the whole vocabulary, and refused only the
  hand-built control carrying a bare `reasoning` string.

The question was not decidable from the committed record alone, and this
is worth recording: the record stores a prompt digest, not a request
pack, so no committed artifact showed what went on the wire. It was also
not decidable by an unkeyed probe — `ollama.com/v1` checks authentication
before it parses the body, so all three candidate shapes return an
identical 401. The credential was the whole of what stood between this
tranche and its answer, and asking for it was the right first move
rather than the last.

**What changed.** No production line. What landed is the pin and the
memory: a mutation-proven regression asserting that no adapter may put a
STRING under `reasoning` (an OBJECT there is accepted, which is why the
rule is about the string and not the key); the measured contract in
`docs/OLLAMA_CLOUD_OPERATIONS.md` §9 with its transcript; a `Traps` entry
in `DR-SUB-llm` for the value-versus-field conflation; and `ERRATA.md`
E76 correcting the premise, with the original ledger left unedited.

**The end-to-end check.** After a green soak, a fresh home rebuilt the
committed launch config's provider profile field for field and ran it.
Setup rc=0, qualification rc=0 on a full battery, and the run reached 29
provider attempts — every one `provider_result` — with 41 artifacts
admitted and accepted and a record that replays valid. So the clause the
alarm predicted would fail is the clause that passed.

**The residue.**

- The relaunch stopped `operational_failure` on a budget denial with
  114 226 of 120 000 tokens spent, where the operator's 2026-08-29 law
  asks for a clean `budget_exhausted`. Parked as P3, unadjudicated: the
  run was an instrument here, not the subject. Continuability, the law's
  other half, does hold.
- The verification probe's own verdict had to be corrected mid-phase. It
  counted a model's HTTP 503 "temporarily overloaded" as a failure of the
  request contract, and reported NOT MET on a run where nothing had been
  refused. Six alternating calls proved the outage independent of the
  field — the no-knob control failed identically — and the verdict now
  separates a contract refusal from an unreachable model, with four
  scripted providers proving it can still fail. Recorded rather than
  quietly fixed, because it is the previous tranche's parked P3 in a new
  place: a measure reporting something other than what it names.
- One probe is one moment. `deepseek-v4-pro` was served in the first run
  and unreachable in the second, hours apart. The contract here is a
  measurement with a date and a re-check command, not a guarantee.
- `deepseek` and `openai` have no committed provider profile, so their
  mappings are pinned by the regression and never measured live. The
  refusal control ran against one model only.

**Accepted does not mean true.** What is established is that on
2026-09-04 the harness's request shape was accepted and one other shape
was not, and that a run built from the committed launch config reached
its seat results. What is not established is that this will hold
tomorrow, which is why the pin is a test and the contract carries the
command that re-derives it.
