import {test, expect} from '@playwright/test';

test('navigate relative URL in new tab', async ({page, context}) => {
  await page.goto('/navigate_new_tab');

  // Set up listener for new page before clicking
  const pagePromise = context.waitForEvent('page');

  // Click button to open in new tab
  await page
    .getByRole('button', {name: 'Open /navigate_new_tab/about in new tab'})
    .click();

  // Wait for new page and verify URL
  const newPage = await pagePromise;
  await newPage.waitForLoadState();
  await expect(newPage).toHaveURL(/.*\/navigate_new_tab\/about/);

  // Verify original page hasn't changed
  await expect(page).toHaveURL(/.*\/navigate_new_tab/);

  // Clean up
  await newPage.close();
});

test('navigate absolute URL in new tab', async ({page, context}) => {
  await page.goto('/navigate_new_tab');

  // Set up listener for new page before clicking
  const pagePromise = context.waitForEvent('page');

  // Click button to open in new tab
  await page.getByRole('button', {name: 'Open example.com in new tab'}).click();

  // Wait for new page and verify URL
  const newPage = await pagePromise;
  await newPage.waitForLoadState();
  await expect(newPage).toHaveURL(/https:\/\/(www\.)?example\.com/);

  // Verify original page hasn't changed
  await expect(page).toHaveURL(/.*\/navigate_new_tab/);

  // Clean up
  await newPage.close();
});

test('navigate with query params in new tab', async ({page, context}) => {
  await page.goto('/navigate_new_tab');

  // Set up listener for new page before clicking
  const pagePromise = context.waitForEvent('page');

  // Click button to open with query params in new tab
  await page.getByRole('button', {name: 'Open with query params'}).click();

  // Wait for new page and verify URL has query params
  const newPage = await pagePromise;
  await newPage.waitForLoadState();
  const url = new URL(newPage.url());
  expect(url.pathname).toContain('/navigate_new_tab/about');
  expect(url.searchParams.get('foo')).toBe('bar');
  expect(url.searchParams.get('baz')).toBe('qux');

  // Verify original page hasn't changed
  await expect(page).toHaveURL(/.*\/navigate_new_tab/);

  // Clean up
  await newPage.close();
});

test('navigate with url query params in new tab', async ({page, context}) => {
  await page.goto('/navigate_new_tab');

  // Set up listener for new page before clicking
  const pagePromise = context.waitForEvent('page');

  // Click button to open with url query params in new tab
  await page.getByRole('button', {name: 'Open with url query params'}).click();

  // Wait for new page and verify URL has query params
  const newPage = await pagePromise;
  await newPage.waitForLoadState();
  const url = new URL(newPage.url());
  expect(url.pathname).toContain('/navigate_new_tab/about');
  expect(url.searchParams.get('foo')).toBeNull();
  expect(url.searchParams.get('baz')).toBeNull();

  // Verify original page hasn't changed
  await expect(page).toHaveURL(/.*\/navigate_new_tab/);

  // Clean up
  await newPage.close();
});

test('traditional same tab navigation still works', async ({page}) => {
  await page.goto('/navigate_new_tab');

  // Click button to navigate in same tab
  await page
    .getByRole('button', {
      name: 'Navigate to /navigate_new_tab/about (same tab)',
    })
    .click();

  // Verify navigation happened in same tab
  await expect(page).toHaveURL(/.*\/navigate_new_tab\/about/);
});
