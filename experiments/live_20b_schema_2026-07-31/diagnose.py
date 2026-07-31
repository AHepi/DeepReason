import sys, traceback; sys.path.insert(0,'/home/user/DeepReason')
from pathlib import Path
import yaml
from deepreason.provider_profile import ProviderProfileV1
from deepreason.preparation import qualification_subject_manifest
from deepreason import qualification as q

raw = yaml.safe_load(Path("home/provider.yaml").read_text())
raw.pop("profile_digest", None); raw.pop("schema", None)
profile = ProviderProfileV1.create(**raw, schema="deepreason-provider-profile.v1")
manifest = qualification_subject_manifest(profile, attached_evidence=True)

def progress(done, total):
    if done % 20 == 0: print(f"  {done}/{total}", flush=True)

try:
    with q.qualification_executor_options(concurrency=4, progress_callback=progress):
        executed = q.default_qualification_executor(manifest)
    import json
    Path("executor_report.json").write_text(json.dumps(executed, indent=1))
    print("EXECUTOR COMPLETED — report written")
except Exception:
    print("EXECUTOR RAISED:")
    traceback.print_exc()
