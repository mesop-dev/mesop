import {test, expect} from '@playwright/test';

test.describe('set_cookie / delete_cookie', () => {
  test('login sets cookie and persists after reload', async ({page}) => {
    await page.goto('/set_cookie');

    // Initial state: not logged in.
    await expect(page.getByText('Not logged in.')).toBeVisible();

    // Click "Log in as Alice".
    await page.getByRole('button', {name: 'Log in as Alice'}).click();

    // After login the UI should show the logged-in state.
    await expect(page.getByText('Logged in as: alice')).toBeVisible();

    // Verify the cookie was actually set by the /__apply-cookies endpoint.
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === 'demo_session');
    expect(sessionCookie).toBeDefined();
    expect(sessionCookie?.value).toBe('user:alice');
    expect(sessionCookie?.httpOnly).toBe(true);

    // Hard-reload: the on_load handler should read the cookie and restore state.
    await page.reload();
    await expect(page.getByText('Logged in as: alice')).toBeVisible();
  });

  test('login state persists in a new tab', async ({page, context}) => {
    await page.goto('/set_cookie');

    // Log in.
    await page.getByRole('button', {name: 'Log in as Alice'}).click();
    await expect(page.getByText('Logged in as: alice')).toBeVisible();

    // Open the same page in a new tab — the cookie should already be present.
    const newPage = await context.newPage();
    await newPage.goto('/set_cookie');
    await expect(newPage.getByText('Logged in as: alice')).toBeVisible();
    await newPage.close();
  });

  test('logout deletes cookie', async ({page}) => {
    await page.goto('/set_cookie');

    // Log in first.
    await page.getByRole('button', {name: 'Log in as Alice'}).click();
    await expect(page.getByText('Logged in as: alice')).toBeVisible();

    // Log out.
    await page.getByRole('button', {name: 'Log out'}).click();
    await expect(page.getByText('Not logged in.')).toBeVisible();

    // Cookie should be gone (or expired with max_age=0).
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === 'demo_session');
    expect(sessionCookie).toBeUndefined();

    // Reload confirms logged-out state is persistent.
    await page.reload();
    await expect(page.getByText('Not logged in.')).toBeVisible();
  });
});
