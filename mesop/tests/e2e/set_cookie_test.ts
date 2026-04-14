import {test, expect} from '@playwright/test';

test.describe('set_cookie / delete_cookie', () => {
  test('/__apply-cookies token is single-use (replay returns 400)', async ({
    page,
  }) => {
    // Intercept the POST to /__apply-cookies and capture the token from the
    // request body so we can attempt a replay after the first use.
    let capturedToken: string | null = null;
    await page.route('**/__apply-cookies', async (route) => {
      const postData = route.request().postData() ?? '';
      const params = new URLSearchParams(postData);
      capturedToken = params.get('t');
      await route.continue();
    });

    await page.goto('/set_cookie');
    await page.getByRole('button', {name: 'Log in as Alice'}).click();
    await expect(page.getByText('Logged in as: alice')).toBeVisible();

    // The token must have been captured by the route interceptor.
    expect(capturedToken).not.toBeNull();

    // Replay the same token — server must reject it with 400.
    const replayResp = await page.request.post(
      page.url().replace(/\/set_cookie.*/, '/__apply-cookies'),
      {form: {t: capturedToken!}},
    );
    expect(replayResp.status()).toBe(400);
  });

  test('login sets cookie and persists after reload', async ({page}) => {
    await page.goto('/set_cookie');

    // Initial state: not logged in.
    await expect(page.getByText('Not logged in.')).toBeVisible();

    // Click "Log in as Alice".
    await page.getByRole('button', {name: 'Log in as Alice'}).click();

    // After login the UI should show the logged-in state.
    await expect(page.getByText('Logged in as: alice')).toBeVisible();

    // Verify the cookie was actually set by the /__apply-cookies endpoint.
    // The @me.cookieclass decorator derives the cookie name from the class
    // name: SessionCookie → session_cookie.
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === 'session_cookie');
    expect(sessionCookie).toBeDefined();
    // Value is JSON-serialised by me.save_cookie().
    expect(JSON.parse(sessionCookie?.value ?? '{}')).toMatchObject({
      username: 'alice',
    });
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
    const sessionCookie = cookies.find((c) => c.name === 'session_cookie');
    expect(sessionCookie).toBeUndefined();

    // Reload confirms logged-out state is persistent.
    await page.reload();
    await expect(page.getByText('Not logged in.')).toBeVisible();
  });
});
