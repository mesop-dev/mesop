from dataclasses import dataclass, field
from typing import Literal

from mesop.exceptions import MesopDeveloperException


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
    allowed_cors_origins: A list of allowed origins for CORS requests, see [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS). Use ["*"] to allow all origins (not recommended for production).
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
  allowed_cors_origins: list[str] = field(default_factory=list)
  dangerously_disable_trusted_types: bool = False

  def __post_init__(self):
    if self.dangerously_disable_trusted_types and self.allowed_trusted_types:
      raise MesopDeveloperException(
        "Cannot disable trusted types and configure allow trusted types on SecurityPolicy at the same time. Set either allowed_trusted_types or dangerously_disable_trusted_types SecurityPolicy parameter."
      )
