"""T5 — the discriminating experiment RESULTS.md named as missing.

Same reviewer, same model, same prompt, same params; two packets differing in
ONE claim. Cell A is the repository's real consistency packet. Cell B is
byte-identical except that CLAUDE.md's excerpt names `scheduler/scheduler.py`
as a frozen surface where INV-frozen-surfaces' excerpt names `qualification.py`
— a flat contradiction between two documents that both appear in the packet.

What this tests: whether an independent model that returned honest verdicts on
truncated input (rung T2) also DETECTS a falsehood, rather than only declining
to certify what it cannot see. A reviewer that passes both cells is not a
referee; it is a rubber stamp with good manners.

max_tokens is 24000 rather than the first run's 6000, and that is NOT FR-15's
"raise the budget" mistake — FR-15's precondition was measured and found
absent. The first run returned empty at finish_reason=length on a packet of
prompt_tokens=1581: the completion cap was spent on 22886 characters of hidden
reasoning before any content was emitted. Shrinking a 1581-token packet would
have addressed nothing.
"""
import sys

sys.path.insert(0, "scripts")
from ollama_transport import OllamaTransport
from review_harness import Job, Slice, run_job, verify_ledger

CORE = """You audit a set of excerpts taken from DIFFERENT documents of one
repository. The excerpts are labelled with the document they came from.

1. The question is NOT whether each claim is true of the world. It is whether
   the excerpts AGREE WITH EACH OTHER. Two documents stating incompatible
   things about the same subject is the defect you are looking for.
2. Work claim by claim. For each subject that appears under more than one
   label, state the subject, quote the competing fragments, and give one
   verdict: AGREE, DISAGREE, or CANNOT_DECIDE.
3. Quote. Never paraphrase a fragment you are calling inconsistent.
4. A difference in wording is not a disagreement. A difference in what is
   asserted - a different list, a different number, a different rule - is.
5. Do not propose rewrites. You are reporting, not editing.

End your reply with exactly one block and nothing after it:
BEGIN_VERDICT
overall: CONSISTENT|INCONSISTENT
disagreements: <n>
worst: "<the single strongest disagreement, quoted, or NONE>"
END_VERDICT"""

TASK = ("Audit these cross-document excerpts for agreement. The repository's "
        "frozen-surface list is stated in more than one document; check it "
        "with particular care.")

CELLS = [
    ("consistency-A-true", "zoo/reviews/CONSISTENCY_PACKET.md"),
    ("consistency-B-planted", "experiments/2026-08-23-treadle-pilot/T5/PLANTED_PACKET.md"),
]

for name, packet in CELLS:
    job = Job(
        name=name,
        role="REVIEWER",
        model="deepseek-v4-pro:0813",
        skill_core=CORE,
        task=TASK,
        inputs=(Slice(packet),),
        out=f"experiments/2026-08-23-treadle-pilot/T5/{name}.md",
        params={"model": "deepseek-v4-pro:0813", "temperature": 0.0, "max_tokens": 24000},
    )
    run_job(job, OllamaTransport, ledger="zoo/reviews/calls.jsonl")
    print(f"ran {name}")

print("ledger rows:", verify_ledger("zoo/reviews/calls.jsonl"))
