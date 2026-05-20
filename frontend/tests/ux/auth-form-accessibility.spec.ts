import { test, expect } from '@playwright/test';

const authInputs = {
  login: ['login-user-id', 'login-password'],
  signup: ['company-name', 'primary-contact', 'admin-email', 'signup-password', 'phone', 'location'],
};

test.describe('Auth form accessibility', () => {
  test('/login inputs have associated labels, names, and autocomplete', async ({ page }) => {
    await page.goto('/login');

    await expect(page.locator('#login-user-id')).toBeVisible();
    await expect(page.locator('label[for="login-user-id"]')).toHaveText(/User ID/i);
    await expect(page.locator('#login-user-id')).toHaveAttribute('name', 'user_id');
    await expect(page.locator('#login-user-id')).toHaveAttribute('autocomplete', 'username');

    await expect(page.locator('#login-password')).toBeVisible();
    await expect(page.locator('label[for="login-password"]')).toHaveText(/Password/i);
    await expect(page.locator('#login-password')).toHaveAttribute('name', 'password');
    await expect(page.locator('#login-password')).toHaveAttribute('autocomplete', 'current-password');
  });

  test('/signup inputs have associated labels and autocomplete', async ({ page }) => {
    await page.goto('/signup');

    const expected = [
      ['company-name', /Company name/i, 'organization'],
      ['primary-contact', /Primary contact/i, 'name'],
      ['admin-email', /Admin email/i, 'email'],
      ['signup-password', /Password/i, 'new-password'],
      ['phone', /Phone/i, 'tel'],
      ['location', /Location/i, 'address-level2'],
    ] as const;

    for (const [id, label, autocomplete] of expected) {
      await expect(page.locator(`#${id}`)).toBeVisible();
      await expect(page.locator(`label[for="${id}"]`)).toHaveText(label);
      await expect(page.locator(`#${id}`)).toHaveAttribute('autocomplete', autocomplete);
    }
  });

  test('auth inputs do not rely on placeholders as the only labeling mechanism', async ({ page }) => {
    for (const [path, ids] of Object.entries(authInputs)) {
      await page.goto(`/${path}`);

      for (const id of ids) {
        const input = page.locator(`#${id}`);
        await expect(input).toBeVisible();
        await expect(page.locator(`label[for="${id}"]`)).toBeVisible();
      }
    }
  });

  test('signup terms link navigates to the public terms page', async ({ page }) => {
    await page.goto('/signup');

    const termsLink = page.getByRole('link', { name: /terms and conditions/i });
    await expect(termsLink).toBeVisible();
    await expect(termsLink).toHaveAttribute('href', '/terms');

    await termsLink.click();
    await expect(page).toHaveURL(/\/terms$/);
    await expect(page.getByRole('heading', { name: /Terms and Conditions/i })).toBeVisible();
  });
});
