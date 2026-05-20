import { test, expect } from '@playwright/test';

/**
 * Mobile-viewport smoke tests for auth pages.
 * Validates that login and signup forms are usable on iPhone SE-sized screens.
 */
const MOBILE_VIEWPORT = { width: 375, height: 812 };

test.use({ viewport: MOBILE_VIEWPORT });

test.describe('Mobile auth pages (375x812)', () => {
  test('/login — login fields and Sign In are visible', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/VeloBid/);

    await expect(page.locator('input[type="text"][placeholder="Enter your user ID"]')).toBeVisible();
    await expect(page.locator('input[type="password"][placeholder="Enter your password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /Sign In/i })).toBeVisible();
  });

  test('/signup — signup fields and Create Account are visible', async ({ page }) => {
    await page.goto('/signup');
    await expect(page).toHaveTitle(/VeloBid/);

    await expect(page.locator('input[name="company_name"]')).toBeVisible();
    await expect(page.locator('input[name="admin_email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /Create Account|Sign Up/i })).toBeVisible();
  });
});
