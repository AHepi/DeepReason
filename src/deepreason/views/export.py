"""Export view: turn a finished run's surviving deliverables into files a
human can open. Read-only over the log/state (the views precedent) except for
writing the requested output directory. Binary-safe: PNGs and other blob
content are copied as raw bytes — programs.content_text would mangle them."""

from pathlib import Path

from deepreason.ontology.state import Status
from deepreason.rules.act import browser_evidence
from deepreason.views.why import why

_EXTENSIONS = {
    "code:html": "html",
    "code:python": "py",
    "code:javascript": "js",
    "json": "json",
    "image/png": "png",
    "csv": "csv",
}


def _raw(harness, artifact) -> bytes:
    if artifact.content_ref.startswith("inline:"):
        return artifact.content_ref[len("inline:"):].encode()
    return harness.blobs.get(artifact.content_ref)


def _extension(codec: str) -> str:
    return _EXTENSIONS.get(codec, "txt")


def _deliverables(harness, artifact_id: str | None) -> list:
    if artifact_id is not None:
        return [harness.state.artifacts[artifact_id]]
    accepted = [
        a for a in harness.state.artifacts.values()
        if harness.state.status.get(a.id) == Status.ACCEPTED
        and (a.provenance.role if a.provenance else "") in ("conjecturer", "synthesizer", "seed")
    ]
    apps = [a for a in accepted if a.codec == "code:html"]
    return apps or [a for a in accepted if str(a.codec).startswith("code:")]


def export_run(harness, out_dir: str | Path, artifact_id: str | None = None) -> list[Path]:
    """Write surviving deliverable artifact(s), their recorded screenshots,
    and a README explaining why each survived. Returns the written paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    readme = ["# DeepReason export", ""]
    for artifact in _deliverables(harness, artifact_id):
        aid = artifact.id
        path = out / f"app-{aid[:12]}.{_extension(str(artifact.codec))}"
        path.write_bytes(_raw(harness, artifact))
        written.append(path)

        status = harness.state.status.get(aid)
        problem_ids = [pid for a, pid in harness.state.addr if a == aid]
        problem = next(
            (harness.state.problems[p] for p in problem_ids if p in harness.state.problems),
            None,
        )
        readme += [f"## {path.name}", ""]
        if problem is not None:
            readme += ["**Problem:**", "", problem.description.strip(), ""]
        readme.append(f"**Status:** {status.value if status else 'unknown'}")
        for payload in browser_evidence(harness, aid):
            readme.append(
                f"**Browser verdict:** {payload['verdict']} "
                f"({payload.get('browser', '?')}, commitment {payload['commitment'][:20]}, "
                f"{len(payload.get('trace', {}).get('steps', []))} script steps)"
            )
            shots_dir = out / "screenshots"
            for sid in payload.get("screenshots", []):
                shot = harness.state.artifacts.get(sid)
                if shot is None:
                    continue
                shots_dir.mkdir(exist_ok=True)
                shot_path = shots_dir / f"{aid[:12]}-{sid[:12]}.png"
                shot_path.write_bytes(_raw(harness, shot))
                written.append(shot_path)
                readme.append(f"- screenshot: `screenshots/{shot_path.name}`")
        vision = [
            e for e in harness.log.read()
            if e.inputs and e.inputs[0] in ("vision-crit", "vision-crit-overridden-by-execution")
            and len(e.inputs) > 1 and e.inputs[1] == aid
        ]
        attacks = [w for w in harness.warrants.values()
                   if w.target == aid and w.id.startswith("w:vision:")]
        if attacks:
            readme.append(f"**Vision critic:** attacked ({len(attacks)} case(s) on record)")
        elif vision:
            readme.append("**Vision critic:** looked at the rendered app, found no fault")
        readme += ["", "**Why it stands (attack/defence chain):**", "", "```",
                   why(aid, harness.state).strip(), "```", ""]
    readme_path = out / "README.md"
    readme_path.write_text("\n".join(readme))
    written.append(readme_path)
    return written


def render_export_summary(paths: list[Path]) -> str:
    return "\n".join(f"wrote {p}" for p in paths)
