import {test, expect} from '@playwright/test';

test('the proper event handler param is used for shared handlers', async ({
  page,
}) => {
  await page.goto('/test_event_disambiguation');

  await page.getByLabel('Input').click();
  await page.getByLabel('Input').fill('abc');
  await page.getByLabel('Input').blur();
  await expect(page.getByText('Input value: abc')).toBeVisible();

  await page.getByRole('combobox').click();
  await page.getByRole('option', {name: 'Option 1'}).click();
  await expect(page.getByText('Select value: opt1')).toBeVisible();

  await page.getByRole('combobox').click();
  await page.getByRole('option', {name: 'Option 2'}).click();
  await expect(page.getByText('Select value: opt2')).toBeVisible();

  await page.getByLabel('Input').click();
  await page.getByLabel('Input').fill('xyz');
  await page.getByLabel('Input').blur();
  await expect(page.getByText('Input value: xyz')).toBeVisible();

  await page.getByRole('combobox').click();
  await page.getByRole('option', {name: 'Option 1'}).click();
  await expect(page.getByText('Select value: opt1')).toBeVisible();
});
