import {test, expect} from '@playwright/test';

test.describe('async onload events', () => {
  test('async generator', async ({page}) => {
    await page.goto('/async_gen');

    await expect(
      page.getByText('Async Generator: Loaded from async generator!'),
    ).toBeVisible();
  });

  test('async coroutine', async ({page}) => {
    await page.goto('/async_coro');

    await expect(
      page.getByText('Async Coroutine: Loaded from coroutine!'),
    ).toBeVisible();
  });
});
