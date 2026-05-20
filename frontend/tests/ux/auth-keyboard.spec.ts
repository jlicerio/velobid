import { test, expect } from '@playwright/test';

test.describe('Auth keyboard UX', () => {
  test('/signup form tabs through fields in logical order from first field', async ({ page }) => {
    await page.goto('/signup');

    await page.locator('#company-name').focus();
    await expect(page.locator('#company-name')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#primary-contact')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#admin-email')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#signup-password')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#phone')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#location')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#accept_terms')).toBeFocused();
  });

  test('/signup terms checkbox toggles with keyboard', async ({ page }) => {
    await page.goto('/signup');

    const checkbox = page.getByRole('checkbox', { name: /terms and conditions/i });
    await checkbox.focus();
    await expect(checkbox).toBeFocused();

    await page.keyboard.press('Space');
    await expect(checkbox).toBeChecked();

    await page.keyboard.press('Space');
    await expect(checkbox).not.toBeChecked();
  });

  test('/login invalid credentials feedback is announced as an alert', async ({ page }) => {
    await page.goto('/login');

    await page.locator('#login-user-id').fill('baduser');
    await page.locator('#login-password').fill('badpass');
    await page.getByRole('button', { name: /Sign In/i }).click();

    const alert = page.getByRole('alert');
    await expect(alert).toHaveText(/Invalid credentials/i);
    await expect(page.locator('#login-user-id')).toHaveAttribute('aria-describedby', 'login-error');
    await expect(page.locator('#login-password')).toHaveAttribute('aria-describedby', 'login-error');
  });
});
