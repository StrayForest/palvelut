const { test, expect } = require("@playwright/test");

for (const width of [360, 1440]) {
  test(`base page is usable at ${width}px with keyboard focus and no console errors`, async ({ page }) => {
    const consoleErrors = [];
    const pageErrors = [];

    page.on("console", (message) => {
      if (message.type() === "error") {
        consoleErrors.push(message.text());
      }
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));

    await page.setViewportSize({ width, height: 900 });
    const response = await page.goto("/palvelut/en/");

    expect(response).not.toBeNull();
    expect(response.status()).toBe(200);
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator("body")).toBeVisible();

    await page.keyboard.press("Tab");
    const skipLink = page.getByRole("link", { name: "Skip to main content" });
    await expect(skipLink).toBeFocused();

    await page.keyboard.press("Enter");
    await expect(page.locator("#main-content")).toBeFocused();

    expect(consoleErrors).toEqual([]);
    expect(pageErrors).toEqual([]);
  });
}
