"""Source package root for blender-addon-framework.

Provides compatibility alias so legacy imports using ``common.*``
resolve to ``src.common.*`` during migration.
"""

from importlib import import_module
import sys


if "common" not in sys.modules:
    sys.modules["common"] = import_module("src.common")
