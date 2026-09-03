"""Reproduce F7 on UNFIXED main: the retry site is unguarded.

Structural, by AST over the module that actually imports -- not a grep,
because `_plan_conjecture_context` appears in prose in this module too.
"""
import ast, inspect, pathlib, textwrap
from deepreason.scheduler.scheduler import Scheduler
import deepreason.rules.conj as conj_mod

src = textwrap.dedent(inspect.getsource(Scheduler.step))
tree = ast.parse(src)

# Every `context_plan = <call>` assignment inside step, in source order.
sites = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "context_plan" for t in n.targets)
]
print("context_plan assignments in Scheduler.step:", len(sites))
for n in sites:
    print(f"  line {n.lineno:>4} (rel):  context_plan = {ast.unparse(n.value)}")

planner_calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and n.func.attr == "_plan_conjecture_context"
]
print("\n_plan_conjecture_context call sites inside step:", len(planner_calls))

# The v6 null-out: is there one guarded assignment of None per planner call?
nullouts = [n for n in sites if isinstance(n.value, ast.Constant) and n.value.value is None]
print("v6 null-outs (context_plan = None):", len(nullouts))

print("\nVERDICT:", end=" ")
if len(planner_calls) == 2 and len(nullouts) == 1:
    print("REPRODUCED -- two planner call sites, only ONE null-out.")
    print("The second (ConjectureContextStale retry) hands conj a live plan.")
else:
    print(f"NOT the diagnosed shape: {len(planner_calls)} planner calls, {len(nullouts)} null-outs")

# What that live plan hits, quoted from the refusing side.
csrc = inspect.getsource(conj_mod.conj)
i = csrc.index("v6 conjecture context must be planned after durable work preparation")
print("\nrules/conj.py guard the retry value reaches:")
print("   ", csrc[:i].rsplit("if ", 1)[-1].splitlines()[0].strip())
print("    raise ValueError(\"v6 conjecture context must be planned after durable work preparation\")")
