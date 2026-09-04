const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const widths = [360, 768, 1440];
const evidenceDir = path.join("test-results", "p2-visual-evidence");

async function capture(page, testInfo, name, url, width, beforeCapture) {
  await page.setViewportSize({ width, height: 800 });
  const response = await page.goto(url);
  expect(response).not.toBeNull();
  expect(response.status()).toBe(200);
  if (beforeCapture) await beforeCapture();

  const hasOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  );
  expect(hasOverflow).toBe(false);

  fs.mkdirSync(evidenceDir, { recursive: true });
  const filename = `${name}-${width}.png`;
  const screenshotPath = path.join(evidenceDir, filename);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach(filename, { path: screenshotPath, contentType: "image/png" });
}

test("P2 responsive visual evidence and design checklist", async ({ page }, testInfo) => {
  test.setTimeout(120_000);

  await page.goto("/palvelut/en/search/?q=accounting");
  const profileHref = await page.locator('a[href*="/professionals/"]').first().getAttribute("href");
  expect(profileHref).toBeTruthy();

  for (const width of widths) {
    await capture(page, testInfo, "home", "/palvelut/en/", width, async () => {
      const search = page.locator("#discovery-search-submit");
      await search.focus();
      await expect(search).toBeFocused();
    });
    if (width === 360) {
      const searchForm = page.locator('form[action$="/search/"]');
      const searchBox = await searchForm.boundingBox();
      expect(searchBox).not.toBeNull();
      expect(searchBox.y).toBeLessThan(800);
    }

    await capture(page, testInfo, "results", "/palvelut/en/search/?q=accounting", width);
    await capture(page, testInfo, "empty", "/palvelut/en/search/?q=definitely-no-provider", width);
    await capture(page, testInfo, "profile", profileHref, width);
    await capture(page, testInfo, "provider-cta", "/palvelut/en/", width, async () => {
      await page.locator("#provider-cta").scrollIntoViewIfNeeded();
    });
  }
});
