// http://localhost:32123/plot
import {expect} from '@playwright/test';
import {testInProdOnly} from './e2e_helpers';

testInProdOnly('csp: default', async ({page}) => {
  const response = await page.goto('/');
  const csp = response?.headers()['content-security-policy']!;
  expect(cleanCsp(csp)).toMatchSnapshot('csp.txt');
});

testInProdOnly('csp: allowed parent iframe origins', async ({page}) => {
  const response = await page.goto('/allowed_iframe_parents');
  const csp = response?.headers()['content-security-policy']!;
  expect(cleanCsp(csp)).toMatchSnapshot('csp_allowed_iframe_parents.txt');
});

testInProdOnly('csp escaping', async ({page}) => {
  const response = await page.goto('/testing/csp_escaping');
  const csp = response?.headers()['content-security-policy']!;
  expect(cleanCsp(csp)).toMatchSnapshot('csp_escaping.txt');
});

testInProdOnly('csp font srcs', async ({page}) => {
  const response = await page.goto('/testing/csp_font_srcs');
  const csp = response?.headers()['content-security-policy']!;
  expect(cleanCsp(csp)).toMatchSnapshot('csp_allowed_font_srcs.txt');
});

testInProdOnly('csp trusted types', async ({page}) => {
  const response = await page.goto('/testing/csp_trusted_types');
  const csp = response?.headers()['content-security-policy']!;
  expect(cleanCsp(csp)).toMatchSnapshot('csp_trusted_types.txt');
});

testInProdOnly('coop: default', async ({page}) => {
  const response = await page.goto('/');
  const coop = response?.headers()['cross-origin-opener-policy']!;
  expect(coop).toEqual('unsafe-none');
});

testInProdOnly('coop: same origin', async ({page}) => {
  const response = await page.goto('/testing/coop_same_origin');
  const coop = response?.headers()['cross-origin-opener-policy']!;
  expect(coop).toEqual('same-origin');
});

testInProdOnly('coop: same origin allow popups', async ({page}) => {
  const response = await page.goto('/testing/coop_same_origin_allow_popups');
  const coop = response?.headers()['cross-origin-opener-policy']!;
  expect(coop).toEqual('same-origin-allow-popups');
});

testInProdOnly('coop: noopener allow popups', async ({page}) => {
  const response = await page.goto('/testing/coop_noopener_allow_popups');
  const coop = response?.headers()['cross-origin-opener-policy']!;
  expect(coop).toEqual('noopener-allow-popups');
});

testInProdOnly('cors: allow all origins', async ({page}) => {
  const response = await page.goto('/testing/cors_allow_all', {
    headers: {
      Origin: 'http://example.com',
    },
  });
  const corsHeader = response?.headers()['access-control-allow-origin'];
  expect(corsHeader).toEqual('*');
});

testInProdOnly('cors: specific origin allowed', async ({page, context}) => {
  const response = await page.goto('/testing/cors_specific_origin', {
    headers: {
      Origin: 'http://example.com',
    },
  });
  const corsHeader = response?.headers()['access-control-allow-origin'];
  expect(corsHeader).toEqual('http://example.com');
  const credentialsHeader =
    response?.headers()['access-control-allow-credentials'];
  expect(credentialsHeader).toEqual('true');
});

testInProdOnly('cors: specific origin not allowed', async ({page}) => {
  const response = await page.goto('/testing/cors_specific_origin', {
    headers: {
      Origin: 'http://notallowed.com',
    },
  });
  const corsHeader = response?.headers()['access-control-allow-origin'];
  expect(corsHeader).toBeUndefined();
});

testInProdOnly('cors: disabled (no headers)', async ({page}) => {
  const response = await page.goto('/testing/cors_disabled', {
    headers: {
      Origin: 'http://example.com',
    },
  });
  const corsHeader = response?.headers()['access-control-allow-origin'];
  expect(corsHeader).toBeUndefined();
});

testInProdOnly('cors: custom headers and methods', async ({page, request}) => {
  // Test preflight OPTIONS request
  const preflightResponse = await request.fetch(
    '/testing/cors_custom_headers',
    {
      method: 'OPTIONS',
      headers: {
        Origin: 'http://example.com',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type, Authorization',
      },
    },
  );

  const allowOrigin = preflightResponse.headers()['access-control-allow-origin'];
  expect(allowOrigin).toEqual('http://example.com');

  const allowMethods = preflightResponse.headers()[
    'access-control-allow-methods'
  ];
  expect(allowMethods).toContain('GET');
  expect(allowMethods).toContain('POST');
  expect(allowMethods).toContain('PUT');
  expect(allowMethods).toContain('DELETE');

  const allowHeaders = preflightResponse.headers()[
    'access-control-allow-headers'
  ];
  expect(allowHeaders).toContain('Content-Type');
  expect(allowHeaders).toContain('Authorization');
  expect(allowHeaders).toContain('X-Custom-Header');

  const maxAge = preflightResponse.headers()['access-control-max-age'];
  expect(maxAge).toEqual('3600');

  const allowCredentials =
    preflightResponse.headers()['access-control-allow-credentials'];
  expect(allowCredentials).toEqual('true');
});

testInProdOnly('cors: expose headers', async ({page}) => {
  const response = await page.goto('/testing/cors_custom_headers', {
    headers: {
      Origin: 'http://example.com',
    },
  });

  const exposeHeaders =
    response?.headers()['access-control-expose-headers'];
  expect(exposeHeaders).toContain('X-Custom-Response-Header');
});

function cleanCsp(csp: string): string {
  return (
    csp
      // nonce is randomly generated so we need to replace it with a stable string.
      .replace(/'nonce-(.*?)'/g, "'nonce-{{NONCE}}'")
      // A bit of formatting to make it easier to read.
      .replace(/; /g, '\n')
  );
}
