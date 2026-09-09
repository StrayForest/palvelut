const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const widths = [360, 390, 768, 1024, 1440];
const evidenceDir = path.join("test-results", "p6-provider-readiness-evidence");

async function capture(page, testInfo, name, url, width) {
  await page.setViewportSize({ width, height: 900 });
  const response = await page.goto(url);
  expect(response).not.toBeNull();
  expect(response.status()).toBe(200);

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

test("brand-new provider can enter self-service without preseeded provider or membership", async ({ page }, testInfo) => {
  test.setTimeout(180_000);

  for (const width of widths) {
    await capture(page, testInfo, "public-provider-cta", "/palvelut/en/", width);
    await capture(page, testInfo, "for-professionals", "/palvelut/en/for-professionals/", width);
    await capture(page, testInfo, "register", "/palvelut/account/register/", width);
    await capture(page, testInfo, "login", "/palvelut/account/login/", width);
  }

  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/palvelut/account/login/");
  await page.getByLabel("Email").fill("provider-fresh-e2e@example.test");
  await page.getByLabel("Password").fill("provider-fresh-e2e-pass");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/palvelut\/account\/profile\/$/);
  await expect(page.locator("#workspace-empty-state")).toBeVisible();

  for (const width of widths) {
    await capture(page, testInfo, "workspace-empty", "/palvelut/account/profile/", width);
    await capture(page, testInfo, "provider-start", "/palvelut/account/provider/start/", width);
  }

  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/palvelut/account/provider/start/");
  await page.getByLabel("Provider type").selectOption("business");
  await page.getByLabel("Legal name").fill("Fresh Browser Provider Oy");
  await page.getByLabel("Display name").fill("Fresh Browser Provider");
  await page.getByLabel("Y-tunnus").fill("1357924-6");
  await page.getByLabel("Evidence kind").selectOption("registry_signatory");
  await page.getByLabel("Evidence reference").fill("Synthetic PRH signatory evidence for browser acceptance");
  await page.getByRole("button", { name: "Send ownership claim" }).click();

  await expect(page).toHaveURL(/\/palvelut\/account\/profile\/$/);
  await expect(page.getByText("Fresh Browser Provider")).toBeVisible();
  await expect(page.getByText(/Ownership claim:\s*Pending/)).toBeVisible();
  await expect(page.getByText("Nothing is public yet")).toBeVisible();

  for (const width of widths) {
    await capture(page, testInfo, "ownership-pending", "/palvelut/account/profile/", width);
  }
});
