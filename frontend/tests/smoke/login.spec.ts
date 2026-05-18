import { test, expect } from '@playwright/test';

/**
 * Login page smoke tests.
 * These run against the deployed VeloBid API (no local webServer).
 */
test.describe('Login page', () => {
  test('redirects / -> /login when unauthenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
    await expect(page).toHaveTitle(/VeloBid/);
  });

  test('renders login form with required fields', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByRole('heading', { name: 'VeloBid' })).toBeVisible();
    await expect(page.getByText('Sign in to your account')).toBeVisible();
    await expect(page.getByRole('textbox', { name: /User ID/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /Password/i })).toBeVisible();

    const signInBtn = page.getByRole('button', { name: /Sign In/i });
    await expect(signInBtn).toBeVisible();
  });

  test('has link to signup page', async ({ page }) => {
    await page.goto('/login');
    const signupLink = page.getByRole('link', { name: /Sign up/i });
    await expect(signupLink).toBeVisible();
    await expect(signupLink).toHaveAttribute('href', /\/signup/);
  });

  test('navigates to signup when signup link is clicked', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('link', { name: /Sign up/i }).click();
    await expect(page).toHaveURL(/\/signup/);
    await expect(page.getByText(/Create your enterprise account/i)).toBeVisible();
  });

  test('signup page has link back to login', async ({ page }) => {
    await page.goto('/signup');
    const signinLink = page.getByRole('link', { name: /Sign in/i });
    await expect(signinLink).toBeVisible();
    await signinLink.click();
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Login error handling', () => {
  test('shows error on empty credentials submit', async ({ page }) => {
    await page.goto('/login');
    const signInBtn = page.getByRole('button', { name: /Sign In/i });

    // Button should be disabled when fields are empty
    await expect(signInBtn).toBeDisabled();
  });

  test('enables sign-in when fields are filled', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('textbox', { name: /User ID/i }).fill('testuser');
    await page.getByRole('textbox', { name: /Password/i }).fill('somepassword');
    const signInBtn = page.getByRole('button', { name: /Sign In/i });
    await expect(signInBtn).toBeEnabled();
  });
});
