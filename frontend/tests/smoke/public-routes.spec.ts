import { test, expect } from '@playwright/test';

/**
 * Public route smoke tests.
 * Validates that login, signup, /terms, /privacy are reachable,
 * and /projects redirects unauthenticated users to /login.
 */
test.describe('Public routes', () => {
  test('GET /login renders login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/VeloBid/);
    await expect(page.getByText(/Sign in/i).first()).toBeVisible();
  });

  test('GET /signup renders signup page', async ({ page }) => {
    await page.goto('/signup');
    await expect(page).toHaveTitle(/VeloBid/);
    await expect(page.getByText(/Sign up|Create|account/i).first()).toBeVisible();
  });

  test('GET /terms does NOT render 404', async ({ page }) => {
    const resp = await page.goto('/terms');
    // Response should not be a 404
    expect(resp?.status()).not.toBe(404);
    // Page body should not contain 404 copy
    await expect(page.getByText(/Page not found/i)).toHaveCount(0);
  });

  test('GET /privacy does NOT render 404', async ({ page }) => {
    const resp = await page.goto('/privacy');
    expect(resp?.status()).not.toBe(404);
    await expect(page.getByText(/Page not found/i)).toHaveCount(0);
  });

  test('GET /projects redirects unauthenticated to /login', async ({ page }) => {
    await page.goto('/projects');
    await expect(page).toHaveURL(/\/login/);
  });
});
