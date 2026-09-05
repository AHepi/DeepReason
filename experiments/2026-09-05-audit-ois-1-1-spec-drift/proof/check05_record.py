"""Check 5, record arm (read-only): every discharge occurrence in a committed
root, and whether any of them changed the epistemic state."""
import sys, json, collections, pathlib
root = pathlib.Path(sys.argv[1])
tags = collections.Counter(); bad = []
n = 0
for line in open(root/'log.jsonl'):
    e = json.loads(line)
    ins = e.get('inputs') or []
    if not (ins and isinstance(ins[0], str) and ins[0].startswith('discharge')):
        continue
    n += 1
    tags[ins[0]] += 1
    sd = e.get('state_diff') or {}
    if e.get('outputs') or sd.get('att+') or sd.get('dep+') or e.get('llm'):
        bad.append((e['seq'], ins[0], e.get('outputs'), sd))
print(f"root                                  : {root}")
print(f"discharge-tagged record events        : {n}")
print(f"tags                                  : {dict(tags)}")
rules = sorted({json.loads(l)["rule"] for l in open(root/"log.jsonl") if "discharge" in l})
print(f"rule of every event mentioning discharge : {rules}")
print(f"discharge events that minted an artifact, an att/dep edge, or an LLM call: {len(bad)}")
for b in bad[:5]: print("   ", b)
