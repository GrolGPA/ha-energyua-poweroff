"""Load integration modules without importing Home Assistant.

The package ``__init__`` imports Home Assistant, which is not needed to test
the pure parsing/schedule code, so a stub package with the right ``__path__``
is registered instead.
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = ROOT / "custom_components" / "energyua_poweroff"

for name, path in (
    ("custom_components", ROOT / "custom_components"),
    ("custom_components.energyua_poweroff", PACKAGE_DIR),
):
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module

sys.path.insert(0, str(ROOT))
