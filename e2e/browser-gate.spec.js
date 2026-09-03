const { test, expect } = require("@playwright/test");

test("Chromium reaches the localized application through Nginx", async ({ page }) => {
  const response = await page.goto("/palvelut/en/");

  expect(response).not.toBeNull();
  expect(response.status()).toBe(200);
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("body")).toBeVisible();
});
