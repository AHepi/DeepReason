"""One byte of log.jsonl altered -> the SECURITY-channel gate must refuse."""
import json, shutil, subprocess, sys, os
from pathlib import Path
from deepreason.runtime.continuation import record_verification_refusal

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src, dst)
log = dst / "log.jsonl"
text = log.read_text(encoding="utf-8")
# Flip one character of a recorded provider endpoint - the same forgery the
# jailbreak tranche used, and the one its gate classifies SECURITY.
import re
m = re.search(r'"endpoint":\s*"([^"]+)"', text)
print("target endpoint:", m.group(1) if m else None)
mutated = text[:m.start(1)] + ("x" if m.group(1)[0] != "x" else "y") + text[m.start(1)+1:]
assert len(mutated) == len(text), "one byte, same length"
log.write_text(mutated, encoding="utf-8")
print("record_verification_refusal ->", record_verification_refusal(dst))
env = {**os.environ, "DEEPREASON_LOOPBACK_SMOKE_KEY": "stub"}
r = subprocess.run([sys.executable, "-m", "deepreason.cli.main", "--root", str(dst),
                    "continue", "--budget", "cycles=2"],
                   capture_output=True, text=True, env=env, timeout=1800)
print("continue rc=", r.returncode, "|", (r.stderr.strip().splitlines() or [""])[-1])
