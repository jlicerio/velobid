import { test, expect } from '@playwright/test';

/**
 * Console-error smoke tests for unauthenticated visits.
 * Ensures that visiting public auth pages does not trigger
 * spurious prefetch errors for authenticated-only resources.
 */
test.describe('Unauthenticated console errors', () => {
  test('visiting /login produces no console error containing projects/with-pricing', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const pricingErrors = errors.filter((e) => e.includes('projects/with-pricing'));
    expect(pricingErrors).toHaveLength(0);
  });

  test('visiting /signup produces no console error containing projects/with-pricing', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/signup');
    await page.waitForLoadState('networkidle');

    const pricingErrors = errors.filter((e) => e.includes('projects/with-pricing'));
    expect(pricingErrors).toHaveLength(0);
  });
});
