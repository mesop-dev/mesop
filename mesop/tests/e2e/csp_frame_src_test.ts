import {expect} from '@playwright/test';
import {testInProdOnly} from './e2e_helpers';

testInProdOnly('CSP frame-src includes blob', async ({page}) => {
  // Listen for CSP violations before navigating
  const cspErrors: string[] = [];
  page.on('console', (msg) => {
    if (
      msg.type() === 'error' &&
      msg.text().includes('Content Security Policy')
    ) {
      cspErrors.push(msg.text());
    }
  });

  // Get the CSP header from the response
  const response = await page.goto('/testing/blob_iframe');
  const headers = response?.headers();
  const cspHeader = headers?.['content-security-policy'];

  // Verify CSP header is present
  expect(cspHeader).toBeDefined();

  // Verify frame-src directive includes blob:
  expect(cspHeader).toContain('frame-src');
  expect(cspHeader).toMatch(/frame-src[^;]*blob:/);

  await page.waitForLoadState('networkidle');

  // No CSP violations should be present
  expect(cspErrors).toHaveLength(0);
});
