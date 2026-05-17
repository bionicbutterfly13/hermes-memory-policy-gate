"""Hermes directory-plugin entry point.

Hermes clones Git plugins into ~/.hermes/plugins/<name> and imports the root
__init__.py. Keep this file dependency-light and route to the package under src/.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent
_SRC = _PLUGIN_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from hermes_memory_policy_gate.plugin import register  # noqa: E402,F401
