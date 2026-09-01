"""Price the two rejected roads: does a MODEL_PROFILE_MISSING compile notice,
or a populated manifest field, move the manifest sha / qualification subject?"""
import json, yaml
from pathlib import Path
from deepreason.config import Config
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import qualification_subject_digest
from deepreason.run_manifest import RunManifest, CompileNoticeV1

MANIFEST = Path("experiments/2026-08-25-change-constructive-frontier/run/run-manifest.json")
raw = json.loads(MANIFEST.read_text())
m = RunManifest.model_validate(raw)
print("schema_version", m.schema_version)

def sha(man): return man.manifest_sha256() if hasattr(man, "manifest_sha256") else None
from deepreason.canonical import sha256_hex
base_bytes = m.canonical_bytes()
print("manifest sha BASE   ", sha256_hex(base_bytes))

# find a provider profile to pair with
prof = None
for p in Path(".").glob("experiments/**/provider.yaml"):
    try:
        prof = ProviderProfileV1.model_validate(yaml.safe_load(p.read_text()))
        print("profile from", p)
        break
    except Exception as e:
        continue
if prof is None:
    print("NO PROVIDER PROFILE FOUND -- subject digest not priced here")
else:
    print("subject BASE        ", qualification_subject_digest(m, prof))

notices = list(m.compile_notices or ())
notices.append(CompileNoticeV1(
    code="MODEL_PROFILE_MISSING",
    message="no model profile document declares glm-5.2",
    pointer="/roles/conjecturer/model",
    resolution="write $DEEPREASON_HOME/model-profiles/glm-5.2/agent.md",
))
withnotice = m.model_copy(update={"compile_notices": tuple(notices)})
print("manifest sha +NOTICE", sha256_hex(withnotice.canonical_bytes()))
if prof is not None:
    print("subject      +NOTICE", qualification_subject_digest(withnotice, prof))
