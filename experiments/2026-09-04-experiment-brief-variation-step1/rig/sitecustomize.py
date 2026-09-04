"""Interpreter hook — the only thing that makes an arm an arm.

On `PYTHONPATH`, Python imports this at startup, before `deepreason` runs. It
does nothing at all unless `DR_ARM` is set, so a stray `PYTHONPATH` cannot
turn an ordinary command into a treatment.

A FAILURE HERE IS LOUD. If the arm cannot be installed the process exits
rather than continuing: a run that quietly fell back to the shipped layout
would cost a full battery and four cycles and report the control's numbers
under the treatment's name -- the exact failure the history tranche's `arm.sh`
earned its `exit 6` guard for.
"""

import os
import sys

if os.environ.get("DR_ARM"):
    try:
        import armrig

        armrig.install()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001 - loud, never silent
        sys.stderr.write(f"ARM RIG FAILED: {type(error).__name__}: {error}\n")
        raise SystemExit(97)
