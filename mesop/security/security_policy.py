from dataclasses import dataclass, field
from typing import Literal

from mesop.exceptions import MesopDeveloperException


@dataclass(kw_only=True)
class CORS:
  """
  A class to configure CORS (Cross-Origin Resource Sharing) settings.

  Attributes:
    allowed_origins: A list of allowed origins for CORS requests.
      Use ["*"] to allow all origins (not recommended for production).
      See [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin).
    allowed_methods: A list of allowed HTTP methods.
      Must specify explicit methods (wildcard "*" is not supported).
      Defaults to ["GET", "POST", "OPTIONS"].
      See [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Methods).
    allowed_headers: A list of allowed headers.
      Use ["*"] to allow all headers, or specify explicit header names.
      See [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Headers).
    expose_headers: A list of headers that can be exposed to the response.
      Must specify explicit headers (wildcard "*" is not supported).
      See [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Expose-Headers).
    allow_credentials: Whether to allow credentials (cookies, authorization headers, etc.).
      Cannot be used with allowed_origins=["*"].
      See [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Credentials).
    max_age: How long (in seconds) the results of a preflight request can be cached.
      Defaults to 86400 (24 hours).
      See [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Max-Age).
  """

  allowed_origins: list[str] = field(default_factory=list)
  allowed_methods: list[str] = field(
    default_factory=lambda: ["GET", "POST", "OPTIONS"]
  )
  allowed_headers: list[str] = field(default_factory=list)
  expose_headers: list[str] = field(default_factory=list)
  allow_credentials: bool = False
  max_age: int = 86400

  def __post_init__(self):
    if self.allow_credentials and "*" in self.allowed_origins:
      raise MesopDeveloperException(
        "Cannot use allow_credentials=True with allowed_origins=['*']. "
        "When credentials are allowed, you must specify explicit origins."
      )
    if "*" in self.allowed_methods:
      raise MesopDeveloperException(
        "Wildcard '*' is not allowed in allowed_methods. "
        "You must specify explicit HTTP methods (e.g., ['GET', 'POST', 'PUT'])."
      )
    if "*" in self.expose_headers:
      raise MesopDeveloperException(
        "Wildcard '*' is not allowed in expose_headers. "
        "You must specify explicit headers to expose."
      )


@dataclass(kw_only=True)
class SecurityPolicy:
  """
  A class to represent the security policy.

  Attributes:
    cross_origin_opener_policy: See [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy).
    allowed_iframe_parents: A list of allowed iframe parents.
    allowed_connect_srcs: A list of sites you can connect to, see [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/connect-src).
    allowed_script_srcs: A list of sites you can load scripts from, see [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/script-src).
    allowed_worker_srcs. A list of sites you can load workers from, see [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/worker-src).
    allowed_trusted_types: A list of trusted type policy names, see [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/trusted-types).
    allowed_font_srcs: A list of sites you can load fonts from, see [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/font-src).
    cors: CORS configuration for cross-origin resource sharing. See [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS).
    dangerously_disable_trusted_types: A flag to disable trusted types.
      Highly recommended to not disable trusted types because
      it's an important web security feature!
  """

  cross_origin_opener_policy: Literal[
    "unsafe-none",
    "same-origin-allow-popups",
    "same-origin",
    "noopener-allow-popups",
  ] = "unsafe-none"
  allowed_iframe_parents: list[str] = field(default_factory=list)
  allowed_connect_srcs: list[str] = field(default_factory=list)
  allowed_script_srcs: list[str] = field(default_factory=list)
  allowed_worker_srcs: list[str] = field(default_factory=list)
  allowed_trusted_types: list[str] = field(default_factory=list)
  allowed_font_srcs: list[str] = field(default_factory=list)
  cors: CORS | None = None
  dangerously_disable_trusted_types: bool = False

  def __post_init__(self):
    if self.dangerously_disable_trusted_types and self.allowed_trusted_types:
      raise MesopDeveloperException(
        "Cannot disable trusted types and configure allow trusted types on SecurityPolicy at the same time. Set either allowed_trusted_types or dangerously_disable_trusted_types SecurityPolicy parameter."
      )
