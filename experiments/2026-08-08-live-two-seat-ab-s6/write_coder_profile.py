"""Write the coder seat's standalone provider profile file.

`deepreason setup --seat GROUP=PATH` binds an EXISTING profile file to a
role group -- it does not build one inline. This writes that file so the
ladder's `setup` call can point `--seat coder=` at it. Settings mirror
`easy.py`'s own "gemma4_31b" preset property_designer entry exactly
(temperature 0.7, max_tokens 4000, provider "ollama", reasoning "none"),
not a fresh guess.
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
print(f"wrote coder profile: {path} digest={profile.profile_digest}")
