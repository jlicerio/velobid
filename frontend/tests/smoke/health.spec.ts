import { test, expect } from '@playwright/test';

/**
 * API health smoke tests via page context.
 * Validates that critical backend endpoints return expected responses.
 */
test.describe('API health endpoints', () => {
  test('/api/v1/health returns ok', async ({ request }) => {
    const resp = await request.get('/api/v1/health');
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toHaveProperty('status', 'ok');
    expect(body).toHaveProperty('service');
  });

  test('/api/v1/meta returns project metadata', async ({ request }) => {
    const resp = await request.get('/api/v1/meta');
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toHaveProperty('project_root');
    expect(body).toHaveProperty('bid_projects_dir');
  });

  test('/api/v1/projects returns 401 when unauthenticated', async ({ request }) => {
    const resp = await request.get('/api/v1/projects');
    expect(resp.status()).toBe(401);
  });

  test('/api/v1/trades returns 401 when unauthenticated', async ({ request }) => {
    const resp = await request.get('/api/v1/trades');
    expect(resp.status()).toBe(401);
  });
});

test.describe('Frontend serves', () => {
  test('index.html loads with VeloBid title', async ({ page }) => {
    const resp = await page.goto('/');
    expect(resp?.status()).toBe(200);
    await expect(page).toHaveTitle(/VeloBid/);
  });

  test('static assets are reachable', async ({ page }) => {
    await page.goto('/');
    // Get the page HTML and look for static asset references
    const html = await page.content();
    const jsMatch = html.match(/src="(\/static\/assets\/[^"]+)"/);
    const cssMatch = html.match(/href="(\/static\/assets\/[^"]+)"/);

    if (jsMatch) {
      const resp = await page.request.get(jsMatch[1]);
      expect(resp.status()).toBe(200);
    }

    if (cssMatch) {
      const resp = await page.request.get(cssMatch[1]);
      expect(resp.status()).toBe(200);
    }
  });
});
