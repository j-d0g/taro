import { test, expect } from '@playwright/test';

test.describe('Taro.ai Frontend', () => {
  test('product grid renders cards', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.product-card');
    const cards = await page.locator('.product-card').count();
    expect(cards).toBeGreaterThan(0);
  });

  test('search filters products', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.product-card');
    const initialCount = await page.locator('.product-card').count();
    await page.fill('#searchInput', 'clinique');
    // Wait for debounce
    await page.waitForTimeout(500);
    const filteredCount = await page.locator('.product-card').count();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
  });

  test('product modal opens on card click', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.product-card');
    await page.locator('.product-card').first().click();
    await expect(page.locator('.modal-overlay')).toHaveClass(/open/);
    await expect(page.locator('.modal-name')).not.toBeEmpty();
  });

  test('product modal closes on X button', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.product-card');
    await page.locator('.product-card').first().click();
    await expect(page.locator('.modal-overlay')).toHaveClass(/open/);
    await page.locator('.modal-close').first().click();
    await expect(page.locator('.modal-overlay')).not.toHaveClass(/open/);
  });

  test('chat panel toggles on bubble click', async ({ page }) => {
    await page.goto('/');
    await page.locator('#chatBubble').click();
    await expect(page.locator('#chatPanel')).toHaveClass(/open/);
    // Close
    await page.locator('.chat-close').click();
    await expect(page.locator('#chatPanel')).not.toHaveClass(/open/);
  });

  test('profile panel opens', async ({ page }) => {
    await page.goto('/');
    await page.locator('#profileBtn').click();
    await expect(page.locator('.profile-overlay')).toHaveClass(/open/);
  });

  test('filter tabs change active state', async ({ page }) => {
    await page.goto('/');
    const beautyTab = page.locator('.filter-tab[data-vertical="Beauty"]');
    await beautyTab.click();
    await expect(beautyTab).toHaveClass(/active/);
    const allTab = page.locator('.filter-tab[data-vertical="All"]');
    await expect(allTab).not.toHaveClass(/active/);
  });

  test('navbar elements are visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.navbar-brand')).toBeVisible();
    await expect(page.locator('#searchInput')).toBeVisible();
    await expect(page.locator('#profileBtn')).toBeVisible();
  });

  test('suggestion chips are visible in chat', async ({ page }) => {
    await page.goto('/');
    await page.locator('#chatBubble').click();
    await expect(page.locator('.suggestion-chip').first()).toBeVisible();
  });
});
