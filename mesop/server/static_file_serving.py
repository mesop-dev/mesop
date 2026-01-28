import gzip
import hashlib
import io
import json
import mimetypes
import os
import re
import secrets
from collections import OrderedDict
from io import BytesIO
from typing import Any, Callable
from urllib.parse import urlparse

from flask import Flask, Response, g, make_response, request, send_file
from werkzeug.security import safe_join

from mesop.env.env import (
  MESOP_BASE_URL_PATH,
  MESOP_HTTP_CACHE_JS_BUNDLE,
  MESOP_WEB_COMPONENTS_HTTP_CACHE_KEY,
  MESOP_WEBSOCKETS_ENABLED,
  get_app_base_path,
)
from mesop.exceptions import MesopException
from mesop.runtime import runtime
from mesop.server.constants import WEB_COMPONENTS_PATH_SEGMENT
from mesop.server.server_utils import (
  get_favicon,
  prefix_base_url,
  remove_base_url_path,
)
from mesop.utils import terminal_colors as tc
from mesop.utils.runfiles import get_runfile_location, has_runfiles
from mesop.utils.url_utils import sanitize_url_for_csp

# mimetypes are not always set correctly, thus manually
# setting the mimetype here.
# See: https://github.com/mesop-dev/mesop/issues/441
mimetypes.add_type("application/javascript", ".js")


def noop():
  pass


def configure_static_file_serving(
  app: Flask,
  static_file_runfiles_base: str,
  livereload_script_url: str | None = None,
  preprocess_request: Callable[[], None] = noop,
  disable_gzip_cache: bool = False,
  default_allowed_iframe_parents: str = "'self'",
):
  def get_path(path: str):
    safe_path = safe_join(static_file_runfiles_base, path)
    assert safe_path
    return get_runfile_location(safe_path)

  prod_bundle_hash = ""
  if MESOP_HTTP_CACHE_JS_BUNDLE and not runtime().debug_mode:
    with open(get_path("prod_bundle.js"), "rb") as f:
      prod_bundle_hash = hashlib.md5(f.read()).hexdigest()

  def retrieve_index_html() -> io.BytesIO | str:
    page_config = runtime().get_page_config(
      path=remove_base_url_path(request.path)
    )
    file_path = get_path("index.html")
    with open(file_path) as file:
      lines = file.readlines()

    for i, line in enumerate(lines):
      if "$$INSERT_CSP_NONCE$$" in line:
        lines[i] = lines[i].replace("$$INSERT_CSP_NONCE$$", g.csp_nonce)
      if "<base href=" in line:
        base_href = prefix_base_url("/")
        lines[i] = re.sub(r'base href=".*?"', f'base href="{base_href}"', line)
      if (
        livereload_script_url
        and line.strip() == "<!-- Inject livereload script (if needed) -->"
      ):
        lines[i] = (
          f'<script src="{livereload_script_url}" nonce={g.csp_nonce}></script>\n'
        )
      if line.strip() == "<!-- Inject favicon -->":
        lines[i] = (
          f'<link rel="shortcut icon" href="{get_favicon()}" type="image/x-icon" />\n'
        )
      if (
        page_config
        and page_config.stylesheets
        and line.strip() == "<!-- Inject stylesheet (if needed) -->"
      ):
        lines[i] = "\n".join(
          [
            f'<link href="{stylesheet}" rel="stylesheet">'
            for stylesheet in page_config.stylesheets
          ]
        )
      if (
        line.strip() == "<!-- Inject experiment settings script (if needed) -->"
      ):
        experiment_settings = {
          "websocketsEnabled": MESOP_WEBSOCKETS_ENABLED,
          "webComponentsCacheKey": MESOP_WEB_COMPONENTS_HTTP_CACHE_KEY,
        }
        lines[i] = f"""
          <script nonce="{g.csp_nonce}">
            window.__MESOP_EXPERIMENTS__ = {json.dumps(experiment_settings)};
            window.__MESOP_BASE_URL_PATH__ = '{MESOP_BASE_URL_PATH}';
          </script>
        """
      if '<script src="prod_bundle.js"' in line and prod_bundle_hash:
        lines[i] = lines[i].replace(
          '<script src="prod_bundle.js"',
          f'<script src="prod_bundle.js?v={prod_bundle_hash}"',
        )

    # Create a BytesIO object from the modified lines
    modified_file_content = "".join(lines)
    binary_file = io.BytesIO(modified_file_content.encode())

    return binary_file

  @app.route(prefix_base_url("/"), strict_slashes=False)
  def serve_root():
    preprocess_request()
    return send_file(retrieve_index_html(), download_name="index.html")

  @app.route(prefix_base_url("/sandbox_iframe.html"))
  def serve_sandbox_iframe():
    preprocess_request()
    return send_file(
      get_path("sandbox_iframe.html"), download_name="sandbox_iframe.html"
    )

  @app.route(prefix_base_url(f"/{WEB_COMPONENTS_PATH_SEGMENT}/<path:path>"))
  def serve_web_components(path: str):
    if not is_file_path(path):
      raise MesopException("Unexpected request to " + path)
    serving_path = (
      get_runfile_location(path)
      if has_runfiles()
      else safe_join(get_app_base_path(), path)
    )

    file_name = os.path.basename(path)
    file_extension = os.path.splitext(file_name)[1].lower()
    allowed_extensions = {".js", ".css"}
    if file_extension not in allowed_extensions:
      raise MesopException(
        f"Unexpected file type: {file_extension}. Only {', '.join(allowed_extensions)} files are allowed."
      )

    if not serving_path:
      raise MesopException("Unexpected request to " + path)
    return send_file_compressed(
      serving_path,
      disable_gzip_cache=disable_gzip_cache,
    )

  @app.route(prefix_base_url("/<path:path>"))
  def serve_file(path: str):
    preprocess_request()
    if is_file_path(path):
      return send_file_compressed(
        get_path(path),
        disable_gzip_cache=disable_gzip_cache,
      )
    else:
      return send_file(retrieve_index_html(), download_name="index.html")

  @app.route(prefix_base_url("/__csp__"), methods=["POST"])
  def csp_report():
    # Get the CSP violation report from the request
    # Flask expects the MIME type to be application/json
    # but it's actually application/csp-report
    report = request.get_json(force=True)

    document_uri: str = report["csp-report"]["document-uri"]
    path = urlparse(document_uri).path
    blocked_uri: str = report["csp-report"]["blocked-uri"]
    # Remove the path from blocked_uri, keeping only the origin.
    blocked_site = (
      urlparse(blocked_uri).scheme + "://" + urlparse(blocked_uri).netloc
    )
    violated_directive: str = report["csp-report"]["violated-directive"]
    if violated_directive == "script-src-elem":
      keyword_arg = "allowed_script_srcs"
    elif violated_directive == "connect-src":
      keyword_arg = "allowed_connect_srcs"
    elif violated_directive == "frame-ancestors":
      keyword_arg = "allowed_iframe_parents"
    elif violated_directive in ("require-trusted-types-for", "trusted-types"):
      keyword_arg = "dangerously_disable_trusted_types"
    else:
      raise Exception("Unexpected CSP violation:", violated_directive, report)
    keyword_arg_value = f"""[
      '{tc.CYAN}{blocked_site}{tc.RESET}',
    ]"""
    if keyword_arg == "dangerously_disable_trusted_types":
      keyword_arg_value = f"{tc.CYAN}True{tc.RESET}"
    print(
      f"""
{tc.RED}⚠️  Content Security Policy Error  ⚠️{tc.RESET}
{tc.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{tc.RESET}
{tc.CYAN}Directive:{tc.RESET}   {tc.GREEN}{violated_directive}{tc.RESET}
{tc.CYAN}Blocked URL:{tc.RESET} {tc.GREEN}{blocked_uri}{tc.RESET}
{tc.CYAN}App path:{tc.RESET}    {tc.GREEN}{path}{tc.RESET}

{tc.YELLOW}ℹ️  If this is coming from your web component,
   update your security policy like this:{tc.RESET}

{tc.MAGENTA}@me.page({tc.RESET}
  {tc.BLUE}security_policy={tc.RESET}{tc.MAGENTA}me.SecurityPolicy({tc.RESET}
    {tc.GREEN}{keyword_arg}={tc.RESET}{keyword_arg_value}
  {tc.MAGENTA}){tc.RESET}
{tc.MAGENTA}){tc.RESET}

{tc.YELLOW}For more info:
{tc.CYAN}https://mesop-dev.github.io/mesop/web-components/troubleshooting/{tc.RESET}
{tc.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{tc.RESET}
"""  # noqa: RUF001
    )

    response = make_response()
    response.status_code = 204
    return response

  @app.before_request
  def generate_nonce():
    g.csp_nonce = secrets.token_urlsafe(16)

  @app.after_request
  def add_security_headers(response: Response):
    page_config = runtime().get_page_config(
      path=remove_base_url_path(request.path)
    )
    # Set X-Content-Type-Options header to prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Set Strict-Transport-Security header to enforce HTTPS
    # All present and future subdomains will be HTTPS for a max-age of 1 year.
    # This blocks access to pages or subdomains that can only be served over HTTP.
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security#examples
    response.headers["Strict-Transport-Security"] = (
      "max-age=31536000; includeSubDomains"
    )

    # Technically order doesn't matter, but it's useful for testing
    # https://stackoverflow.com/a/77850553
    csp = OrderedDict(
      {
        "default-src": "'self'",
        "font-src": "'self' fonts.gstatic.com data:",
        # Mesop app developers should be able to iframe other sites from various origins.
        "frame-src": "* blob:",
        # Mesop app developers should be able to load images and media from various origins.
        "img-src": "'self' data: https: http: blob:",
        "media-src": "'self' data: https: blob:",
        # Need 'unsafe-inline' because we apply inline styles for our components.
        # This is also used by Angular for animations:
        # https://github.com/angular/angular/pull/55260
        # Finally, other third-party libraries like Plotly rely on setting stylesheets dynamically.
        "style-src": "'self' 'unsafe-inline' fonts.googleapis.com",
        "script-src": f"'self' 'nonce-{g.csp_nonce}'",
        # https://angular.io/guide/security#enforcing-trusted-types
        "trusted-types": "angular angular#unsafe-bypass lit-html highlight.js",
        "require-trusted-types-for": "'script'",
        "report-uri": prefix_base_url("/__csp__"),
      }
    )
    if page_config and page_config.stylesheets:
      csp["style-src"] += " " + " ".join(
        [sanitize_url_for_csp(url) for url in page_config.stylesheets]
      )
    security_policy = None
    if page_config and page_config.security_policy:
      security_policy = page_config.security_policy

    if security_policy and security_policy.cross_origin_opener_policy:
      response.headers["Cross-Origin-Opener-Policy"] = (
        security_policy.cross_origin_opener_policy
      )

    if security_policy and security_policy.allowed_connect_srcs:
      csp["connect-src"] = "'self' " + " ".join(
        [
          sanitize_url_for_csp(url)
          for url in security_policy.allowed_connect_srcs
        ]
      )
    if security_policy and security_policy.allowed_script_srcs:
      csp["script-src"] += " " + " ".join(
        [
          sanitize_url_for_csp(url)
          for url in security_policy.allowed_script_srcs
        ]
      )
    if security_policy and security_policy.allowed_worker_srcs:
      csp["worker-src"] = "'self' " + " ".join(
        [
          sanitize_url_for_csp(url)
          for url in security_policy.allowed_worker_srcs
        ]
      )
    if security_policy and security_policy.allowed_font_srcs:
      csp["font-src"] += " " + " ".join(
        [sanitize_url_for_csp(url) for url in security_policy.allowed_font_srcs]
      )
    if security_policy and security_policy.allowed_trusted_types:
      csp["trusted-types"] += " " + " ".join(
        security_policy.allowed_trusted_types
      )
    if security_policy and security_policy.dangerously_disable_trusted_types:
      del csp["trusted-types"]
      del csp["require-trusted-types-for"]

    if runtime().debug_mode:
      # Allow all origins in debug mode (aka editor mode) because
      # when Mesop is running under Colab, it will be served from
      # a randomly generated origin.
      csp["frame-ancestors"] = "*"
    elif security_policy and security_policy.allowed_iframe_parents:
      csp["frame-ancestors"] = "'self' " + " ".join(
        [
          sanitize_url_for_csp(url)
          for url in security_policy.allowed_iframe_parents
        ]
      )
    else:
      csp["frame-ancestors"] = default_allowed_iframe_parents

    if livereload_script_url:
      livereload_origin = extract_origin(livereload_script_url)
      if livereload_origin:
        if "connect-src" in csp:
          csp["connect-src"] += f" {livereload_origin}"
        else:
          csp["connect-src"] = f"'self' {livereload_origin}"

    if request.path == prefix_base_url("/sandbox_iframe.html"):
      # Set a minimal CSP to not restrict Mesop app developers.
      # Need frame-ancestors to ensure other sites do not iframe
      # this page and exploit it.
      csp_subset = OrderedDict({"frame-ancestors": csp["frame-ancestors"]})
      response.headers["Content-Security-Policy"] = "; ".join(
        [key + " " + value for key, value in csp_subset.items()]
      )
    else:
      # Set Content-Security-Policy header to restrict resource loading
      # Based on https://angular.io/guide/security#content-security-policy
      response.headers["Content-Security-Policy"] = "; ".join(
        [key + " " + value for key, value in csp.items()]
      )

    # Set Referrer-Policy header to control referrer information
    # Recommended by https://web.dev/articles/referrer-best-practices
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if (
      request.path == prefix_base_url("/prod_bundle.js")
      and request.args.get("v") == prod_bundle_hash
      and not runtime().debug_mode
      and MESOP_HTTP_CACHE_JS_BUNDLE
    ):
      response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    if (
      request.path.startswith(
        prefix_base_url(f"/{WEB_COMPONENTS_PATH_SEGMENT}/")
      )
      and not runtime().debug_mode
      and MESOP_WEB_COMPONENTS_HTTP_CACHE_KEY
      and request.args.get("v") == MESOP_WEB_COMPONENTS_HTTP_CACHE_KEY
    ):
      response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    if "Cache-Control" not in response.headers:
      # no-store ensures that resources are never cached.
      # https://web.dev/articles/http-cache#request-headers
      response.headers["Cache-Control"] = "no-store"

    return response


def is_file_path(path: str) -> bool:
  _, last_segment = os.path.split(path)
  return "." in last_segment


# To avoid paying the cost of gzipping the same file multiple times
# we have a singleton cache from file path to gzipped bytes.
gzip_cache: dict[str, bytes] = {}


def send_file_compressed(path: str, disable_gzip_cache: bool) -> Any:
  response = send_file(path)
  response.headers["Content-Encoding"] = "gzip"
  response.direct_passthrough = False
  if path in gzip_cache:
    gzip_data = gzip_cache[path]
  else:
    gzip_buffer = BytesIO()
    with gzip.GzipFile(
      mode="wb", fileobj=gzip_buffer, compresslevel=6
    ) as gzip_file:
      gzip_file.write(response.get_data())
    gzip_buffer.seek(0)
    gzip_data = gzip_buffer.getvalue()
    if not disable_gzip_cache:
      gzip_cache[path] = gzip_data

  response.set_data(gzip_data)
  response.headers["Content-Length"] = str(len(response.get_data()))
  return response


def extract_origin(livereload_script_url: str) -> str | None:
  match = re.search(r"localhost:\d+", livereload_script_url)
  if match:
    return match.group()
  # If we couldn't extract an origin, return None
  return None
