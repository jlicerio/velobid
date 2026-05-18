import { test, expect } from '@playwright/test';

/**
 * Signup page smoke tests.
 * These run against the deployed VeloBid API.
 */
test.describe('Signup page', () => {
  test('renders signup form with all fields', async ({ page }) => {
    await page.goto('/signup');

    await expect(page.getByRole('heading', { name: 'VeloBid' })).toBeVisible();
    await expect(page.getByText(/Create your enterprise account/i)).toBeVisible();

    // Required fields
    await expect(page.getByRole('textbox', { name: /Company name/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /Primary contact/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /Admin email/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /Password/i })).toBeVisible();

    // Optional fields
    await expect(page.getByRole('textbox', { name: /Phone/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /Location/i })).toBeVisible();

    // Terms checkbox
    await expect(page.getByRole('checkbox', { name: /terms/i })).toBeVisible();

    // Submit button
    await expect(page.getByRole('button', { name: /Create Account/i })).toBeVisible();
  });

  test('submit disabled until terms accepted', async ({ page }) => {
    await page.goto('/signup');

    await page.getByRole('textbox', { name: /Company name/i }).fill('Test Corp');
    await page.getByRole('textbox', { name: /Primary contact/i }).fill('Jane Doe');
    await page.getByRole('textbox', { name: /Admin email/i }).fill('jane@test.com');
    await page.getByRole('textbox', { name: /Password/i }).fill('SecurePass123');

    // Button should be disabled without terms
    const btn = page.getByRole('button', { name: /Create Account/i });
    await expect(btn).toBeDisabled();

    // Accept terms
    await page.getByRole('checkbox', { name: /terms/i }).check();
    await expect(btn).toBeEnabled();
  });
});

test.describe('Signup happy path', () => {
  test('completes signup and reaches email-sent screen', async ({ page }) => {
    const timestamp = Date.now();
    await page.goto('/signup');

    await page.getByRole('textbox', { name: /Company name/i }).fill(`QA Smoke ${timestamp}`);
    await page.getByRole('textbox', { name: /Primary contact/i }).fill('QA Tester');
    await page.getByRole('textbox', { name: /Admin email/i }).fill(`qa-smoke-${timestamp}@example.com`);
    await page.getByRole('textbox', { name: /Password/i }).fill('SecurePass123');
    await page.getByRole('textbox', { name: /Phone/i }).fill('+1 555 010 2026');
    await page.getByRole('textbox', { name: /Location/i }).fill('McAllen, TX');
    await page.getByRole('checkbox', { name: /terms/i }).check();

    await page.getByRole('button', { name: /Create Account/i }).click();

    // Should reach email verification screen
    await expect(page.getByText(/Check your email/i)).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Verification email sent/i)).toBeVisible();
    await expect(page.getByText(/qa-smoke-/)).toBeVisible();
    await expect(page.getByText(/30 minutes/i)).toBeVisible();

    // Return to sign-in link
    await expect(page.getByRole('link', { name: /Return to Sign In/i })).toBeVisible();
  });
});

test.describe('Signup validation', () => {
  test('rejects invalid email format', async ({ page }) => {
    await page.goto('/signup');

    await page.getByRole('textbox', { name: /Company name/i }).fill('Test');
    await page.getByRole('textbox', { name: /Primary contact/i }).fill('Jane');
    await page.getByRole('textbox', { name: /Admin email/i }).fill('not-an-email');
    await page.getByRole('textbox', { name: /Password/i }).fill('SecurePass123');
    await page.getByRole('checkbox', { name: /terms/i }).check();

    await page.getByRole('button', { name: /Create Account/i }).click();

    // Should show validation error
    await expect(page.getByText(/email/i)).toBeVisible({ timeout: 10000 });
  });

  test('rejects short password', async ({ page }) => {
    await page.goto('/signup');

    await page.getByRole('textbox', { name: /Company name/i }).fill('Test');
    await page.getByRole('textbox', { name: /Primary contact/i }).fill('Jane');
    await page.getByRole('textbox', { name: /Admin email/i }).fill('jane@test.com');
    await page.getByRole('textbox', { name: /Password/i }).fill('short');
    await page.getByRole('checkbox', { name: /terms/i }).check();

    await page.getByRole('button', { name: /Create Account/i }).click();

    // Should show password validation error
    await expect(page.getByText(/8/i)).toBeVisible({ timeout: 10000 });
  });
});
