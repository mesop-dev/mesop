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
    // Include the Origin header so the CSRF check passes; only the
    // single-use token check should fire (returning 400).
    // Use pathname replacement rather than a full-URL regex so that any
    // MESOP_BASE_URL_PATH prefix is preserved.
    const currentUrl = new URL(page.url());
    const replayUrl = new URL(currentUrl.toString());
    replayUrl.pathname = replayUrl.pathname.replace(
      /\/set_cookie$/,
      '/__apply-cookies',
    );
    const replayResp = await page.request.post(replayUrl.toString(), {
      form: {t: capturedToken!},
      headers: {Origin: currentUrl.origin},
    });
    expect(replayResp.status()).toBe(400);
  });

  test('login sets cookie and persists after reload', async ({page}) => {
    await page.goto('/set_cookie');
    await expect(page.getByText('Not logged in.')).toBeVisible();

    // Set up listener before click so no request can slip by.
    const applyCookiesResponse = page.waitForResponse('**/__apply-cookies');
    await page.getByRole('button', {name: 'Log in as Alice'}).click();

    // A 204 response from /__apply-cookies confirms the Set-Cookie header was
    // sent to the browser (a 400 would mean the token was invalid or missing).
    const resp = await applyCookiesResponse;
    expect(resp.status()).toBe(204);
    await expect(page.getByText('Logged in as: alice')).toBeVisible();

    // Hard-reload: me.cookie(SessionCookie) in on_load reads the stored cookie
    // and restores the logged-in state.  This proves end-to-end that:
    //   • the cookie name matches what me.cookie() looks up (session_cookie)
    //   • the JSON value was stored and parsed correctly (username == "alice")
    //   • the cookie survives a full browser reload
    await page.reload();
    await expect(page.getByText('Logged in as: alice')).toBeVisible();
  });

  test('login state persists in a new tab', async ({page, context}) => {
    await page.goto('/set_cookie');

    // Log in and wait for the cookie to be set before opening a new tab.
    const applyCookies = page.waitForResponse('**/__apply-cookies');
    await page.getByRole('button', {name: 'Log in as Alice'}).click();
    await applyCookies;
    await expect(page.getByText('Logged in as: alice')).toBeVisible();

    // Open the same page in a new tab — the cookie should already be present.
    const newPage = await context.newPage();
    await newPage.goto('/set_cookie');
    await expect(newPage.getByText('Logged in as: alice')).toBeVisible();
    await newPage.close();
  });

  test('logout deletes cookie', async ({page}) => {
    await page.goto('/set_cookie');

    // Log in first and wait for the cookie to be set.
    const loginCookies = page.waitForResponse('**/__apply-cookies');
    await page.getByRole('button', {name: 'Log in as Alice'}).click();
    await loginCookies;
    await expect(page.getByText('Logged in as: alice')).toBeVisible();

    // Log out and wait for the deletion cookie to be applied.
    const logoutCookies = page.waitForResponse('**/__apply-cookies');
    await page.getByRole('button', {name: 'Log out'}).click();
    await logoutCookies;
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
