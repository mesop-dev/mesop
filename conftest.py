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
  """Stub mesop.protos.ui_pb2 and all component-level *_pb2 modules.

  This is a no-op when the real Bazel-generated proto modules are already
  importable (e.g. inside a Bazel test run), so it won't shadow them.
  """
  # If the real protobuf module is importable, the Bazel build has already
  # made all *_pb2 modules available — don't install any stubs.
  try:
    import mesop.protos.ui_pb2  # noqa: F401

    return
  except ImportError:
    pass

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
  # Appended (not inserted) so that real modules on sys.path take precedence.
  sys.meta_path.append(_Pb2Finder())


class _Pb2Finder:
  """Meta path finder that returns a MagicMock for any mesop.*_pb2 module.

  Restricted to the ``mesop.`` namespace to avoid shadowing real protobuf
  modules (e.g. ``google.protobuf.*_pb2``).  Uses the modern ``find_spec`` /
  ``create_module`` / ``exec_module`` importlib API instead of the deprecated
  ``find_module`` / ``load_module`` pair.
  """

  def find_spec(self, fullname: str, path=None, target=None):
    import importlib.util

    if fullname.startswith("mesop.") and fullname.endswith("_pb2"):
      return importlib.util.spec_from_loader(fullname, loader=self)  # type: ignore[arg-type]
    return None

  def create_module(self, spec):
    # Return a MagicMock as the module object — Python's import machinery
    # stores this in sys.modules[spec.name] so attribute access just works.
    return MagicMock()

  def exec_module(self, module):
    pass  # MagicMock is already fully set up by create_module


def _stub_mesop_package() -> None:
  """Replace mesop's top-level package with a lightweight stub.

  This prevents mesop/__init__.py from running (it imports every component
  and their Bazel-generated proto files).  The stub's __path__ points at
  the real mesop/ directory so submodule imports still resolve correctly.

  This is a no-op when the real Bazel-generated proto modules are already
  importable (same condition used by _stub_generated_protos), because in
  that environment mesop/__init__.py can run successfully without stubs.
  """
  if "mesop" in sys.modules:
    return
  # If real proto modules are importable we're inside a Bazel build that has
  # already generated them — don't shadow the real package.
  try:
    import mesop.protos.ui_pb2  # noqa: F401

    return
  except ImportError:
    pass
  stub = types.ModuleType("mesop")
  stub.__path__ = [os.path.join(_REPO_ROOT, "mesop")]  # type: ignore[attr-defined]
  stub.__package__ = "mesop"
  stub.__file__ = os.path.join(_REPO_ROOT, "mesop", "__init__.py")
  sys.modules["mesop"] = stub


# Run all stubs before any test module is imported.
_stub_bazel_modules()
_stub_generated_protos()
_stub_mesop_package()
