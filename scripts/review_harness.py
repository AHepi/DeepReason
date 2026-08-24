#!/usr/bin/env python3
"""External-model review calls: packet governor + hash-chained ledger.

Field reports FR-15, FR-16, FR-17 made this module. It is evidence-gathering,
never acceptance: it calls an external model, so its output has no exit-code
authority over any artifact. What it guarantees is auditability -- the exact
bytes each model was shown can be rechecked -- and the governor rules that
keep a review answerable.

DESIGN
- A Job is a role, a model tag (DATED tags only), a task, and a tuple of
  Slices (named, bounded regions of named files). The packet is assembled
  only from slices, so isolation is checkable: Job.forbidden lists files the
  packet must never contain, and assembly refuses if a slice names one.
- PACKET GOVERNOR (FR-15): a packet over Job.packet_ceiling characters is
  refused before any call, with the remedy named: shrink the packet (extract
  claims; see consistency_packet.py), never raise the output budget.
- TRANSPORT IS INJECTED. This file ships no network code and no credential
  handling. run_job(job, transport) takes any callable
  (system, user, params) -> reply_text. NullTransport is provided for smoke
  tests. Your real transport reads its key from the process environment ONLY.
- LEDGER (LEDGER_FORMAT.md): one JSONL row per call, hash-chained via
  prev_sha256 over the previous row's exact bytes. Superseded semantics
  (FR-17): a re-run overwrites its transcript; the ledger keeps every row;
  verify_ledger checks the transcript against the LATEST row for its path
  and requires digests on every row, superseded included.
- PROVENANCE, NOT REPRODUCIBILITY (FR-16): every transcript header carries
  "reproducibility: none". temperature/seed record configuration, not
  replayability; identical packets have returned different replies.
"""
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PACKET_CEILING = 24000


def sha256(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


class HarnessError(ValueError):
    pass


@dataclass(frozen=True)
class Slice:
    path: str
    start: str = None
    stop: str = None

    def render(self, root):
        body = (root / self.path).read_text(encoding="utf-8")
        if self.start is not None:
            if self.start not in body:
                raise HarnessError(f"slice start {self.start!r} not in {self.path}")
            body = body[body.index(self.start):]
        if self.stop is not None:
            if self.stop not in body:
                raise HarnessError(f"slice stop {self.stop!r} not in {self.path}")
            body = body[: body.index(self.stop)]
        return body.rstrip() + "\n"

    def label(self):
        bounds = ""
        if self.start is not None or self.stop is not None:
            bounds = f" [{self.start or 'start'} .. {self.stop or 'end'})"
        return f"{self.path}{bounds}"


@dataclass(frozen=True)
class Job:
    name: str
    role: str
    model: str
    skill_core: str
    task: str
    inputs: tuple
    out: str
    params: dict = field(default_factory=lambda: {"temperature": 0.0, "seed": 17,
                                                  "max_tokens": 24000})
    forbidden: tuple = ()
    packet_ceiling: int = DEFAULT_PACKET_CEILING

    def system(self):
        return (f"{self.skill_core}\n\nYour role in this run is: {self.role}.\n"
                "You are an independent auditor. Answer only from the material "
                "you are given; if it does not settle a question, say so in the "
                "protocol's own vocabulary rather than guessing.")

    def user(self, root):
        for item in self.inputs:
            if item.path in self.forbidden:
                raise HarnessError(
                    f"job {self.name}: slice names forbidden file {item.path}")
        parts = [self.task, ""]
        for item in self.inputs:
            parts.append(f"===== BEGIN {item.label()} =====")
            parts.append(item.render(root))
            parts.append(f"===== END {item.label()} =====")
            parts.append("")
        packet = "\n".join(parts)
        if len(packet) > self.packet_ceiling:
            raise HarnessError(
                f"job {self.name}: packet is {len(packet)} chars against a "
                f"{self.packet_ceiling} ceiling. Shrink the packet -- extract "
                "the claims (consistency_packet.py) or tighten the slices. Do "
                "NOT raise the output budget; it is the wrong knob (FR-15)")
        return packet


def NullTransport(system, user, params):
    """Smoke-test transport: no network, deterministic, obviously fake."""
    return (f"NULL-TRANSPORT REPLY\nsystem_sha256={sha256(system)}\n"
            f"prompt_sha256={sha256(user)}\n")


def _last_row(ledger_path):
    if not ledger_path.exists():
        return None, "GENESIS"
    lines = [l for l in ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        return None, "GENESIS"
    return json.loads(lines[-1]), sha256(lines[-1])


def run_job(job, transport, root=None, ledger="calls.jsonl"):
    root = Path(root or Path.cwd())
    system, user = job.system(), job.user(root)
    reply = transport(system, user, job.params)
    header = (f"<!-- job={job.name} model={job.model} role={job.role} -->\n"
              f"<!-- params={json.dumps(job.params, sort_keys=True)} -->\n"
              f"<!-- reproducibility: none -- params are provenance, not a "
              f"replay guarantee (FR-16) -->\n"
              f"<!-- prompt_sha256={sha256(user)} -->\n"
              f"<!-- inputs: {'; '.join(i.label() for i in job.inputs)} -->\n\n")
    out_path = root / job.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + reply, encoding="utf-8")

    ledger_path = root / ledger
    last, prev = _last_row(ledger_path)
    row = {
        "seq": (last["seq"] + 1) if last else 1,
        "prev_sha256": prev,
        "job": job.name, "model": job.model, "role": job.role,
        "params": job.params,
        "system_sha256": sha256(system), "prompt_sha256": sha256(user),
        "reply_sha256": sha256(reply), "reply_chars": len(reply),
        "out": job.out,
    }
    with open(ledger_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return row


CREDENTIAL_MARKERS = ("api_key", "authorization", "Bearer ")


def _split_transcript(text):
    """Header (leading comment lines + one blank) and the reply body."""
    lines = text.splitlines(keepends=True)
    index = 0
    while index < len(lines) and lines[index].startswith("<!--"):
        index += 1
    if index < len(lines) and lines[index].strip() == "":
        index += 1
    return "".join(lines[:index]), "".join(lines[index:])


def verify_ledger(ledger, root=None):
    """Raise HarnessError on any violation; return row count when clean."""
    root = Path(root or Path.cwd())
    ledger_path = root / ledger
    if not ledger_path.exists():
        raise HarnessError(f"{ledger} does not exist")
    lines = [l for l in ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    prev = "GENESIS"
    latest_by_out = {}
    for index, line in enumerate(lines, 1):
        for marker in CREDENTIAL_MARKERS:
            if marker in line:
                raise HarnessError(f"row {index} carries credential material")
        row = json.loads(line)
        if row["seq"] != index:
            raise HarnessError(f"row {index}: seq {row['seq']} not contiguous")
        if row["prev_sha256"] != prev:
            raise HarnessError(f"row {index}: hash chain broken")
        for key in ("prompt_sha256", "reply_sha256", "system_sha256"):
            if not str(row.get(key, "")).startswith("sha256:"):
                raise HarnessError(f"row {index}: missing digest {key}")
        latest_by_out[row["out"]] = row
        prev = sha256(line)
    for out, row in sorted(latest_by_out.items()):
        transcript_path = root / out
        if not transcript_path.exists():
            raise HarnessError(f"transcript {out} missing for its latest row")
        transcript = transcript_path.read_text(encoding="utf-8")
        header, reply = _split_transcript(transcript)
        if row["prompt_sha256"] not in header:
            raise HarnessError(
                f"transcript {out} does not match its LATEST ledger row "
                "(a superseded transcript, or tampering)")
        if "reproducibility: none" not in header:
            raise HarnessError(f"transcript {out} missing the FR-16 header line")
        # The reply digest must MATCH the transcript's reply bytes, not merely
        # exist. Found by FR-18 applied to this very module: the last row of
        # the chain has no successor to protect its bytes, so without this
        # check a tampered reply_sha256 -- or a tampered reply -- on the
        # latest row was accepted. A digest that is checked against nothing
        # is decoration.
        if sha256(reply) != row["reply_sha256"]:
            raise HarnessError(
                f"transcript {out}: reply does not match the ledger's "
                "reply_sha256 (tampered reply, or tampered row)")
    return len(lines)


if __name__ == "__main__":
    print(__doc__.strip().splitlines()[0])
    print("Library module: import and inject a transport. NullTransport smoke:")
    print(NullTransport("s", "u", {}).splitlines()[0])
