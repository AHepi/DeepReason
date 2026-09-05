"""Measure what a mini import actually pulls in, against SPEC.md S1's lists."""
import json, subprocess, sys

FENCED = ["deepreason.scheduler","deepreason.qualification","deepreason.capabilities",
          "deepreason.amendment","deepreason.bridge","deepreason.evaluation",
          "deepreason.adjudication","deepreason.application.text_runs","deepreason.calculus",
          "deepreason.workflow.transaction_service","deepreason.schools"]
ALLOWED = ["deepreason.harness","deepreason.ontology","deepreason.log.event_log",
           "deepreason.invariants","deepreason.programs","deepreason.informal.skeleton",
           "deepreason.rules.guards","deepreason.rules.warrants","deepreason.run_manifest",
           "deepreason.llm.wire","deepreason.llm.contracts","deepreason.llm.firewall",
           "deepreason.llm.profiles"]

def closure(mods):
    prog = ("import importlib, sys, json\n"
            "for m in %r: importlib.import_module(m)\n"
            "print(json.dumps(sorted({f for f in %r for k in sys.modules "
            "if k == f or k.startswith(f + '.')})))\n" % (mods, FENCED))
    out = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(out.stderr[-2000:])
    return json.loads(out.stdout.strip().splitlines()[-1])

allowed_only = closure(ALLOWED)
with_mini = closure(["minireason.loop"])
print("ARM A  allowed record modules alone pull in:")
for m in allowed_only: print("   ", m)
print("ARM B  importing minireason.loop pulls in:")
for m in with_mini: print("   ", m)
print("ARM C  what MINI adds beyond ARM A:", sorted(set(with_mini) - set(allowed_only)))
