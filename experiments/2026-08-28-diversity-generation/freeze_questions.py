#!/usr/bin/env python3
"""Write question_digests.json.  Run once, at freeze; the driver asserts
against the committed file and refuses to run on any drift."""
import hashlib
import json
import pathlib

from questions import QUESTIONS

out = {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in sorted(QUESTIONS.items())}
path = pathlib.Path(__file__).with_name("question_digests.json")
path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps(out, indent=2, sort_keys=True))
