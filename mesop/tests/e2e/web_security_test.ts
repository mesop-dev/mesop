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

function cleanCsp(csp: string): string {
  return (
    csp
      // nonce is randomly generated so we need to replace it with a stable string.
      .replace(/'nonce-(.*?)'/g, "'nonce-{{NONCE}}'")
      // A bit of formatting to make it easier to read.
      .replace(/; /g, '\n')
  );
}
