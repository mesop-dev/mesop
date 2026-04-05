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

## Cross-site WebSocket Hijacking (CSWSH)

Unlike regular HTTP requests, browsers do **not** enforce same-origin policy for WebSocket connections. This means a malicious page on another origin could open a WebSocket to your Mesop server and interact with it on behalf of a logged-in user.

To prevent this, Mesop validates the `Origin` header on every WebSocket upgrade request and rejects connections whose origin does not match the server's own URL. This check mirrors the existing CSRF protection on the SSE (`POST /__ui__`) endpoint.

The check is skipped in [debug mode](./debugging.md) to support environments like Colab where the UI and the server may run on different origins.

### Deployments behind a reverse proxy

If your app is deployed behind a reverse proxy (Cloud Run, App Engine, Kubernetes, nginx, etc.), the server's apparent URL may differ from the external-facing URL seen by browsers. In that case the origin check could incorrectly reject legitimate connections.

Mesop solves this by reading the `X-Forwarded-Proto` and `X-Forwarded-Host` headers set by the proxy, but only when proxy-header trust is enabled. See [Trusting proxy forwarding headers](./deployment.md#trusting-proxy-forwarding-headers) in the deployment guide for details.

## API

You can configure the security policy at the page level. See [SecurityPolicy on the Page API docs](../api/page.md#mesop.security.security_policy.SecurityPolicy).
