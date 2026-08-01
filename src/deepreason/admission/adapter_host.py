"""In-sandbox adapter host: raw bytes on stdin, one closed JSON result out.

This module runs as ``python -m deepreason.admission.adapter_host
<module>:<callable>`` inside the containment wrapper.  By the time it
imports the adapter, CPU and memory rlimits apply and network syscalls are
denied, so an adapter cannot phone home, read the clock into its output
deterministically enough to matter, or exceed its bounds — purity is a
property of the cage, not a promise.
"""

from __future__ import annotations

import importlib
import json
import sys


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1 or ":" not in arguments[0]:
        sys.stderr.write("adapter host requires exactly one module:callable\n")
        return 2
    module_name, _, attribute = arguments[0].partition(":")
    data = sys.stdin.buffer.read()
    try:
        module = importlib.import_module(module_name)
        extract = getattr(module, attribute)
        result = extract(data)
    except Exception as error:  # noqa: BLE001 - the boundary result is typed
        sys.stderr.write(f"{type(error).__name__}: {error}\n")
        return 3
    payload = result.model_dump(mode="json", by_alias=True, exclude_none=True)
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a subprocess
    raise SystemExit(main())
