const { test, expect } = require("@playwright/test");

test("Chromium reaches the application through Nginx", async ({ page }) => {
  const response = await page.goto("/");

  expect(response).not.toBeNull();
  expect(response.status()).toBe(200);
  await expect(page.locator("body")).toBeVisible();
});
