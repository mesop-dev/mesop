import {test, expect} from '@playwright/test';

test('navigate with open_in_new_tab - relative URL', async ({page, context}) => {
  await page.goto('/navigate_new_tab');

  // Get the current pages before clicking
  const pagesBefore = context.pages().length;

  // Click button to open about page in new tab
  await page.getByRole('button', {name: 'Open about page in new tab'}).click();

  // Wait for new tab to open
  await context.waitForEvent('page');

  // Check that a new page was opened
  const pagesAfter = context.pages().length;
  expect(pagesAfter).toBe(pagesBefore + 1);

  // Get the new page
  const newPage = context.pages()[pagesAfter - 1];

  // Wait for navigation in new tab
  await newPage.waitForURL('**/about');

  // Verify the content in the new page
  expect(await newPage.getByText('About Page').textContent()).toContain(
    'About Page',
  );

  // Verify original page is still on the same URL
  expect(page.url()).toContain('/navigate_new_tab');
});

test('navigate with open_in_new_tab - external URL', async ({
  page,
  context,
}) => {
  await page.goto('/navigate_new_tab');

  // Get the current pages before clicking
  const pagesBefore = context.pages().length;

  // Click button to open external URL in new tab
  await page
    .getByRole('button', {name: 'Open external URL in new tab'})
    .click();

  // Wait for new tab to open
  await context.waitForEvent('page');

  // Check that a new page was opened
  const pagesAfter = context.pages().length;
  expect(pagesAfter).toBe(pagesBefore + 1);

  // Get the new page
  const newPage = context.pages()[pagesAfter - 1];

  // Wait for navigation in new tab to Google
  await newPage.waitForURL('https://google.com/**', {timeout: 5000});

  // Verify original page is still on the same URL
  expect(page.url()).toContain('/navigate_new_tab');
});

test('navigate with open_in_new_tab false - same tab', async ({page}) => {
  await page.goto('/navigate_new_tab');

  // Click button to open about page in same tab
  await page
    .getByRole('button', {name: 'Open about page in same tab'})
    .click();

  // Wait for navigation in same tab
  await page.waitForURL('**/about');

  // Verify the content changed in the same tab
  expect(await page.getByText('About Page').textContent()).toContain(
    'About Page',
  );
});

test('navigate with query params in new tab', async ({page, context}) => {
  await page.goto('/navigate_new_tab');

  // Get the current pages before clicking
  const pagesBefore = context.pages().length;

  // Click button to open with query params in new tab
  await page
    .getByRole('button', {name: 'Open with query params in new tab'})
    .click();

  // Wait for new tab to open
  await context.waitForEvent('page');

  // Check that a new page was opened
  const pagesAfter = context.pages().length;
  expect(pagesAfter).toBe(pagesBefore + 1);

  // Get the new page
  const newPage = context.pages()[pagesAfter - 1];

  // Wait for navigation in new tab
  await newPage.waitForURL('**/query_params?search=test&page=1');

  // Verify query params are in the URL
  expect(newPage.url()).toContain('search=test');
  expect(newPage.url()).toContain('page=1');

  // Verify original page is still on the same URL
  expect(page.url()).toContain('/navigate_new_tab');
});
