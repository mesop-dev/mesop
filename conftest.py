"""Root conftest.py — runs before any test collection.

Stubs the mesop package and Bazel-generated modules so that unit tests
can run with plain pytest without a Bazel build.

The key trick: we put a lightweight stub for the top-level ``mesop``
package into sys.modules *before* pytest tries to import any test module.
This prevents mesop/__init__.py (which transitively imports hundreds of
Bazel-generated component proto files) from ever being executed.
Submodules (mesop.commands.*, mesop.exceptions, etc.) are still importable
as real modules because our stub carries the correct __path__.
"""

import os
import sys
import types
from unittest.mock import MagicMock

_REPO_ROOT = os.path.dirname(__file__)


def _stub_bazel_modules() -> None:
  """Stub Bazel-only packages that are not available via pip."""
  for mod in (
    "rules_python",
    "rules_python.python",
    "rules_python.python.runfiles",
  ):
    if mod not in sys.modules:
      m = MagicMock()
      m.__path__ = []
      sys.modules[mod] = m


def _stub_generated_protos() -> None:
  """Stub mesop.protos.ui_pb2 and all component-level *_pb2 modules."""
  # Parent proto package
  if "mesop.protos" not in sys.modules:
    pkg = types.ModuleType("mesop.protos")
    pkg.__path__ = []  # type: ignore[attr-defined]
    sys.modules["mesop.protos"] = pkg

  if "mesop.protos.ui_pb2" not in sys.modules:
    sys.modules["mesop.protos.ui_pb2"] = MagicMock()

  # Component-level *_pb2 modules (e.g. accordion_pb2, button_pb2, ...) are
  # imported by mesop/components/**/*.py.  We register a blanket finder so
  # any import matching mesop.*_pb2 returns a MagicMock automatically.
  sys.meta_path.insert(0, _Pb2Finder())


class _Pb2Finder:
  """Meta path finder that returns a MagicMock for any *_pb2 module."""

  def find_module(self, fullname: str, path=None):  # legacy interface
    if fullname.endswith("_pb2"):
      return self
    return None

  def load_module(self, fullname: str):
    if fullname not in sys.modules:
      sys.modules[fullname] = MagicMock()
    return sys.modules[fullname]


def _stub_mesop_package() -> None:
  """Replace mesop's top-level package with a lightweight stub.

  This prevents mesop/__init__.py from running (it imports every component
  and their Bazel-generated proto files).  The stub's __path__ points at
  the real mesop/ directory so submodule imports still resolve correctly.
  """
  if "mesop" in sys.modules:
    return
  stub = types.ModuleType("mesop")
  stub.__path__ = [os.path.join(_REPO_ROOT, "mesop")]  # type: ignore[attr-defined]
  stub.__package__ = "mesop"
  stub.__file__ = os.path.join(_REPO_ROOT, "mesop", "__init__.py")
  sys.modules["mesop"] = stub


# Run all stubs before any test module is imported.
_stub_bazel_modules()
_stub_generated_protos()
_stub_mesop_package()
