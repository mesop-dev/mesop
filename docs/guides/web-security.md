# Web Security

## Static file serving

Mesop allows serving JS and CSS files located within the Mesop app's file subtree to support [web components](../web-components/index.md).

**Security Warning:** Do not place any sensitive or confidential JS and CSS files in your Mesop project directory. These files may be inadvertently exposed and served by the Mesop web server, potentially compromising your application's security.

## JavaScript Security

At a high-level, Mesop is built on top of Angular which provides [built-in security protections](https://angular.io/guide/security) and Mesop configures a strict [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP).

Specifics:

- Mesop APIs do not allow arbitrary JavaScript execution in the main execution context. For example, the [markdown](../components/markdown.md) component sanitizes the markdown content and removes active HTML content like JavaScript.
- Mesop's default Content Security Policy prevents arbitrary JavaScript code from executing on the page unless it passes [Angular's Trusted Types](https://angular.io/guide/security#enforcing-trusted-types) polices.

## Iframe Security

To prevent [clickjacking](https://owasp.org/www-community/attacks/Clickjacking), Mesop apps, when running in prod mode (the default mode used when [deployed](../guides/deployment.md)), do not allow sites from any other origins to iframe the Mesop app.

> Note: pages from the same origin as the Mesop app can always iframe the Mesop app.

If you want to allow a trusted site to iframe your Mesop app, you can explicitly allow list the [sources](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors#sources) which can iframe your app by configuring the security policy for a particular page.

### Example

```py
import mesop as me


@me.page(
  path="/allows_iframed",
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://google.com"],
  ),
)
def app():
  me.text("Test CSP")
```

You can also use wildcards to allow-list multiple subdomains from the same site, such as: `https://*.example.com`.

## Cross Origin Opener Policy

Mesop sets this value to `unsafe-none`, which is the default value. It is recommended to set this to `same-origin` to ensure process isolation from random domains. In most cases, your Mesop app should run without any issues.

For more information, see [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy) and [XS Leaks Wiki](https://xsleaks.dev/).

## CORS (Cross-Origin Resource Sharing)

By default, Mesop apps do not set CORS headers, which means they can only be accessed from the same origin. If you want to allow your Mesop app to be embedded or accessed from other origins (e.g., as a widget on another website), you can configure CORS by providing a `CORS` configuration object to the security policy.

### Example: Allow all origins

```py
import mesop as me


@me.page(
  path="/cors_enabled",
  security_policy=me.SecurityPolicy(
    cors=me.CORS(
      allowed_origins=["*"],
    ),
  ),
)
def app():
  me.text("This page can be accessed from any origin")
```

> **Warning:** Using `allowed_origins=["*"]` allows any origin to access your Mesop app. This is not recommended for production applications that handle sensitive data.

### Example: Allow specific origins with credentials

```py
import mesop as me


@me.page(
  path="/cors_enabled",
  security_policy=me.SecurityPolicy(
    cors=me.CORS(
      allowed_origins=["https://example.com", "https://app.example.com"],
      allow_credentials=True,
    ),
  ),
)
def app():
  me.text("This page can be accessed from example.com and app.example.com")
```

### Example: Advanced CORS configuration

For more control over CORS behavior, you can configure additional options:

```py
import mesop as me


@me.page(
  path="/api",
  security_policy=me.SecurityPolicy(
    cors=me.CORS(
      allowed_origins=["https://example.com"],
      allowed_methods=["GET", "POST", "PUT", "DELETE"],
      allowed_headers=["Content-Type", "Authorization", "X-Custom-Header"],
      expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Reset"],
      allow_credentials=True,
      max_age=3600,  # Cache preflight response for 1 hour
    ),
  ),
)
def app():
  me.text("API endpoint with custom CORS configuration")
```

### CORS Configuration Options

The `me.CORS` class supports the following parameters:

- **allowed_origins**: List of origins that can access the resource. Use `["*"]` to allow all origins (cannot be used with `allow_credentials=True`).
- **allowed_methods**: List of HTTP methods allowed for CORS requests. Can use `["*"]` to allow all methods (but not with `allow_credentials=True`). Defaults to `["GET", "POST", "OPTIONS"]`.
- **allowed_headers**: List of headers that can be used in the actual request. Use `["*"]` to allow all headers (can be used even with credentials).
- **expose_headers**: List of headers that browsers are allowed to access from the response. Can use `["*"]` to expose all headers (but not with `allow_credentials=True`).
- **allow_credentials**: Whether to allow credentials (cookies, authorization headers, etc.). When `True`, wildcard `"*"` cannot be used in `allowed_origins`, `allowed_methods`, or `expose_headers`.
- **max_age**: How long (in seconds) the results of a preflight request can be cached. Defaults to 86400 (24 hours).

Mesop automatically handles preflight OPTIONS requests when CORS is configured.

For more information about CORS, see [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS).

## API

You can configure the security policy at the page level. See [SecurityPolicy on the Page API docs](../api/page.md#mesop.security.security_policy.SecurityPolicy).
