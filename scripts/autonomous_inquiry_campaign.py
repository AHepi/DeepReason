#!/usr/bin/env python
"""Run or audit a multi-wave autonomous-inquiry campaign.

The input plan is a ``campaign.plan.v2`` JSON document.  Relative run roots
and working directories are resolved relative to the plan file::

    {
      "schema": "campaign.plan.v2",
      "qualification": true,
      "waves": [
        {"id": "A", "runs": [
          {
            "id": "A1",
            "root": "runs/A1",
            "reasoning_command": ["deepreason", "reason", "..."],
            "bridge_command": ["deepreason", "bridge", "..."]
          }
        ]}
      ]
    }

Omit a command to audit an already-existing root without launching it.
"""

from deepreason.experiments.campaign_cli import main


if __name__ == "__main__":
    raise SystemExit(main())
