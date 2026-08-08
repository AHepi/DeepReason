"""Write Block A's CROSS-cell conjecture-seat profile (gemma4:31b on
Ollama Cloud). Identical shape to S6's write_coder_profile.py -- the
file is just a provider profile; only the seat GROUP it gets bound to
at `deepreason setup --seat conjecture=<this file>` differs from S6's
`--seat coder=<this file>`.
"""

import sys

from deepreason.provider_profile import ProviderProfileV1, write_provider_profile

profile = ProviderProfileV1.create(
    provider="ollama",
    endpoint="https://ollama.com/v1",
    model_id="gemma4:31b",
    family="gemma",
    context_window_tokens=131072,
    maximum_completion_tokens=8192,
    credential_env="OLLAMA_API_KEY",
    reasoning="none",
    temperature=0.7,
)
path = write_provider_profile(profile, sys.argv[1])
print(f"wrote cross-cell conjecture profile: {path} digest={profile.profile_digest}")
