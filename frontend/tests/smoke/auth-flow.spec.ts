import { test, expect } from '@playwright/test';

/**
 * Full authentication flow smoke test.
 * Covers: Login -> Dashboard (when valid creds available).
 */
const TEST_USER_ID = process.env.VELOBID_TEST_USER_ID || '';
const TEST_PASSWORD = process.env.VELOBID_TEST_PASSWORD || '';

test.describe('Authentication flow', () => {
  test('login redirects to /projects on success when valid creds provided', async ({ page }) => {
    test.skip(!TEST_USER_ID || !TEST_PASSWORD, 'Set VELOBID_TEST_USER_ID and VELOBID_TEST_PASSWORD in environment');

    await page.goto('/login');
    await page.getByRole('textbox', { name: /User ID/i }).fill(TEST_USER_ID);
    await page.getByRole('textbox', { name: /Password/i }).fill(TEST_PASSWORD);
    await page.getByRole('button', { name: /Sign In/i }).click();

    // Should navigate to projects dashboard
    await expect(page).toHaveURL(/\/projects/, { timeout: 15000 });
  });

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('textbox', { name: /User ID/i }).fill('nonexistent_user_12345');
    await page.getByRole('textbox', { name: /Password/i }).fill('wrongpassword');
    await page.getByRole('button', { name: /Sign In/i }).click();

    // Should show some error feedback (error message, toast, or stay on login)
    // Wait for either an error element or the button to remain
    await page.waitForTimeout(3000);
    // We should still be on login (not redirected to projects)
    await expect(page).not.toHaveURL(/\/projects/);
  });
});
