import json, pathlib
from deepreason.run_manifest import RunManifest
paths = sorted(pathlib.Path("experiments").rglob("run-manifest.json"))
moved = []
for p in paths:
    raw = p.read_text()
    m = RunManifest.model_validate_json(raw)
    a = json.dumps(json.loads(raw), sort_keys=True, separators=(",", ":"))
    b = json.dumps(m.model_dump(mode="json", by_alias=True), sort_keys=True, separators=(",", ":"))
    if a != b: moved.append(str(p))
print(f"{len(paths)} manifests, {len(moved)} differ")
for x in moved: print("  ", x)
