"""Path setup: minireason lives in mini/, the parent in src/ (needed only
by the subset-reader and graduation fixtures)."""

import sys
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
for p in (str(MINI), str(MINI.parent / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)
