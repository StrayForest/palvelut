const { test, expect } = require("@playwright/test");

test("provider completes onboarding on mobile without staff edits", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });

  await page.goto("/palvelut/account/login/");
  await page.getByLabel(/username/i).fill("mobile-onboarding@example.test");
  await page.getByLabel(/password/i).fill("test-only-pass");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/palvelut\/account\/profile\/$/);
  await expect(page.getByRole("heading", { name: "Provider workspace" })).toBeVisible();
  await expect(page.getByText("Mobile Onboarding Draft", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(360);

  await page.getByRole("link", { name: "Edit profile" }).click();
  await expect(page.getByRole("heading", { name: "Edit Mobile Onboarding Draft" })).toBeVisible();

  await page.getByLabel("Legal name").fill("Mobile Onboarding Complete Oy");
  await page.getByLabel("Display name").fill("Mobile Onboarding Complete");
  await page.getByLabel("Y tunnus").fill("1234567-8");
  await page.getByRole("button", { name: "Save draft" }).click();

  await expect(page.getByLabel("Display name")).toHaveValue("Mobile Onboarding Complete");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(360);

  await page.getByRole("link", { name: "Preview" }).click();
  await expect(page.getByRole("heading", { name: "Mobile Onboarding Complete" })).toBeVisible();
  await page.getByRole("button", { name: "Submit for review" }).click();

  await expect(page).toHaveURL(/\/palvelut\/account\/profile\/\?submitted=1$/);
  await expect(page.getByRole("status")).toHaveText("Profile submitted for review.");
  await expect(page.getByText(/Status: Pending review/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(360);
});
