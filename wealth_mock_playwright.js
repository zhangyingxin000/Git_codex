// Set WEALTH_MOCK_FILE to one of mocks/wealth-level/*.json before running.
const { test, expect } = require('@playwright/test');
const fs = require('fs');

test('财富等级页面使用指定模拟响应', async ({ page }) => {
  const mockFile = process.env.WEALTH_MOCK_FILE;
  if (!mockFile) throw new Error('WEALTH_MOCK_FILE is required');
  const payload = JSON.parse(fs.readFileSync(mockFile, 'utf8'));
  await page.route('**/level/exeperience/v2/get**', route => route.fulfill({
    status: payload.code === 401 ? 401 : 200,
    contentType: 'application/json',
    body: JSON.stringify(payload)
  }));
  await page.goto(process.env.APP_URL);
  await page.waitForResponse(r => r.url().includes('/level/exeperience/v2/get'));
  await expect(page.locator('body')).toBeVisible();
  // Platform-generated UI assertions are appended per requirement and scenario.
});
