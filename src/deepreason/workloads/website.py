"""Compatibility adapter around the existing website state machine."""

import json
from pathlib import Path


class WebsiteWorkloadAdapter:
    profile = "website"
    pack_profile = "website.v1"
    progress_phases = (
        "plan",
        "design",
        "component-build",
        "assemble",
        "browser-validate",
        "export",
    )

    @staticmethod
    def workflow_class():
        from deepreason.workflows.website import WebsiteWorkflow

        return WebsiteWorkflow

    def completion(self, root: Path | str) -> bool:
        path = Path(root) / "website-terminal.json"
        if not path.exists():
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("outcome") == "completed"


WEBSITE_WORKLOAD = WebsiteWorkloadAdapter()
