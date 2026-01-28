import {expect, test} from '@playwright/test';

test('CSP frame-src includes blob and scf.usercontent.goog', async ({page}) => {
  // Navigate to any page
  await page.goto('/testing/blob_iframe');

  // Get the CSP header from the response
  const response = await page.goto('/testing/blob_iframe');
  const headers = response?.headers();
  const cspHeader = headers?.['content-security-policy'];

  // Verify CSP header is present
  expect(cspHeader).toBeDefined();

  // Verify frame-src directive includes blob: and *.scf.usercontent.goog
  expect(cspHeader).toContain('frame-src');
  expect(cspHeader).toMatch(/frame-src[^;]*blob:/);
  expect(cspHeader).toMatch(/frame-src[^;]*https:\/\/\*\.scf\.usercontent\.goog/);

  // Also verify the page loads without CSP errors
  const cspErrors: string[] = [];
  page.on('console', (msg) => {
    if (
      msg.type() === 'error' &&
      msg.text().includes('Content Security Policy')
    ) {
      cspErrors.push(msg.text());
    }
  });

  await page.waitForLoadState('networkidle');

  // No CSP violations should be present
  expect(cspErrors).toHaveLength(0);
});
