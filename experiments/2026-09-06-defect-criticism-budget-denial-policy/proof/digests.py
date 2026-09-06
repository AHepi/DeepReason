"""Does the new Config field move any digest a run's identity rests on?

Run from the repository root.  Prints the six manifest source-config hashes
and the qualification subject digest.  The whole point of the versioned-source
drop line is that these are BYTE-IDENTICAL before and after the field exists.
"""

import json
import sys

sys.path.insert(0, ".")

from tests.test_reusable_qualification import _manifest, _profile  # noqa: E402

from deepreason.config import Config  # noqa: E402

profile = _profile()
manifest = _manifest(profile)
echo = json.loads(manifest.engine_config_json)

leaked = sorted(k for k in echo if "CRITICISM_BUDGET" in k)
print("leaked into engine_config_json:", leaked)
print("source_config_hash:", manifest.source_config_hash)
print("manifest sha256:    ", manifest.sha256)
print("field present on Config:", hasattr(Config(), "CRITICISM_BUDGET_DENIAL_POLICY"))
