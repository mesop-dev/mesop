import os

from dotenv import find_dotenv, load_dotenv

from mesop.exceptions import MesopDeveloperException

if os.environ.get("BUILD_WORKSPACE_DIRECTORY"):
  # If running with Bazel, we look for `mesop/.env` from the root workspace.
  load_dotenv()
else:
  # Try to load .env file for PyPi Mesop build which should be in the user's current
  # working directory.
  load_dotenv(find_dotenv(usecwd=True))

MESOP_APP_BASE_PATH = os.environ.get("MESOP_APP_BASE_PATH", "")
if MESOP_APP_BASE_PATH:
  if not os.path.isabs(MESOP_APP_BASE_PATH):
    raise MesopDeveloperException(
      f"MESOP_APP_BASE_PATH must be an absolute path, but got {MESOP_APP_BASE_PATH} instead."
    )
  if not os.path.isdir(MESOP_APP_BASE_PATH):
    raise MesopDeveloperException(
      f"MESOP_APP_BASE_PATH is not a valid directory: {MESOP_APP_BASE_PATH}"
    )

MESOP_BASE_URL_PATH = os.environ.get("MESOP_BASE_URL_PATH", "").strip()
if MESOP_BASE_URL_PATH:
  if not MESOP_BASE_URL_PATH.startswith("/"):
    raise MesopDeveloperException("MESOP_BASE_URL_PATH must start with a slash")
  MESOP_BASE_URL_PATH = MESOP_BASE_URL_PATH.rstrip("/")


def get_app_base_path() -> str:
  if not MESOP_APP_BASE_PATH:
    return os.getcwd()
  return MESOP_APP_BASE_PATH


def get_base_url_path() -> str:
  return MESOP_BASE_URL_PATH


MESOP_PROD_UNREDACTED_ERRORS = (
  os.environ.get("MESOP_PROD_UNREDACTED_ERRORS", "false").lower() == "true"
)

MESOP_WEBSOCKETS_ENABLED = (
  os.environ.get("MESOP_WEBSOCKETS_ENABLED", "false").lower() == "true"
)

MESOP_HTTP_CACHE_JS_BUNDLE = (
  os.environ.get("MESOP_HTTP_CACHE_JS_BUNDLE", "false").lower() == "true"
)

MESOP_WEB_COMPONENTS_HTTP_CACHE_KEY = os.environ.get(
  "MESOP_WEB_COMPONENTS_HTTP_CACHE_KEY", None
)

# Trust reverse-proxy forwarding headers (X-Forwarded-Proto, X-Forwarded-Host, etc.).
# Auto-enabled on known managed cloud platforms (Cloud Run, App Engine, Kubernetes).
# Set MESOP_TRUST_PROXY_HEADERS=true to enable explicitly for other proxied deployments.
MESOP_TRUST_PROXY_HEADERS = (
  os.environ.get("MESOP_TRUST_PROXY_HEADERS", "false").lower() == "true"
  or bool(os.environ.get("K_SERVICE"))  # Google Cloud Run
  or bool(os.environ.get("GAE_APPLICATION"))  # Google App Engine
  or bool(os.environ.get("KUBERNETES_SERVICE_HOST"))  # Kubernetes
)
