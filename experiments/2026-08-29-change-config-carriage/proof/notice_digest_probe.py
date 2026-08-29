"""Does adding an optional notice field move a manifest that carries an
UNRELATED notice? The subject payload KEEPS non-NOT_CARRIED notices."""
import sys, json
from deepreason.config import Config
from deepreason.run_manifest import CompileNoticeV1, RunManifest, compile_run_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import qualification_subject_digest
from deepreason.preparation import qualification_subject_manifest

profile = ProviderProfileV1.create(
    provider="openai", endpoint="https://api.example.com/v1", model_id="model-a",
    model_revision="rev-a", family="family-a", context_window_tokens=262144,
    maximum_completion_tokens=4096, credential_env="K")

m = qualification_subject_manifest(profile, config=Config())
# graft an UNRELATED notice on, the way a real compile would
notice = CompileNoticeV1(code="SOME_OTHER_NOTICE", message="m", pointer="/p")
m2 = m.model_copy(update={"compile_notices": (notice,)})
print("notice dump      :", json.dumps(notice.model_dump(mode="json"), sort_keys=True))
print("manifest sha256  :", m2.sha256)
print("subject digest   :", qualification_subject_digest(m2, profile))
