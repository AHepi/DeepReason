"""Check 3, record arm: does the SHIPPED default critic pack put a status
label in front of a seat?  Read-only against a committed root."""
import sys, pathlib
from deepreason.harness import Harness
from deepreason.llm import packs

root = pathlib.Path(sys.argv[1])
h = Harness(root, read_only=True)
st = h.state
targets = {}
for x, t in sorted(st.att):
    targets.setdefault(t, []).append(x)
tid = max(targets, key=lambda t: len(targets[t]))
print(f"root            : {root}")
print(f"artifacts       : {len(st.artifacts)}")
print(f"attack edges    : {len(st.att)}")
print(f"target chosen   : {tid}  ({len(targets[tid])} standing attackers)")
print(f"attacker labels : "
      + ", ".join(f"{x[:12]}={st.status.get(x).value if st.status.get(x) else '?'}"
                  for x in targets[tid][:6]))
text = packs.render_batch_crit_pack([tid], st, h.commitments, h.blobs, token_budget=4000)
i = text.lower().find("standing attacks")
print("\n--- verbatim slice of the pack the shipped default critic layout renders ---")
print(text[i:i+600] if i >= 0 else "(no standing-attacks section rendered)")
