import re, pathlib
# Anchored to this file, not to the worktree it was written in: an
# artifact whose purpose is re-derivation must re-derive where it lands.
REPO = pathlib.Path(__file__).resolve().parents[3]
src = REPO / 'src' / 'deepreason'
body = (REPO / 'docs/map/SEAM-llm-x-verification.md').read_text()
sources = [(f, f.read_text(errors='ignore')) for f in sorted(src.rglob('*.py')) if '__pycache__' not in str(f)]
spec = 'attempt_trace|split_legs && LLMAttempt|LLMSplitLegV1'
field, other = (p.strip() for p in spec.split('&&', 1))
field_re, other_re = re.compile(field), re.compile(other)
enforce_re = re.compile(rf"(?:{field})\s*(?:!=|==)|(?:!=|==)\s*[\w.]*(?:{field})|raise[^\n]*(?:{field})")
cand = enf = 0
for f, text in sources:
    if not (field_re.search(text) and other_re.search(text)):
        continue
    cand += 1
    e = bool(enforce_re.search(text))
    if e:
        enf += 1
    named = (f.name in body) or (str(f.relative_to(REPO)) in body)
    print(f"{'ENFORCE' if e else 'reader ':8} {'named' if named else 'UNNAMED':7} {f.relative_to(REPO)}")
print(f"candidates={cand} enforcement={enf}")
