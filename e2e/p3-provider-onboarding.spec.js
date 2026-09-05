const { test, expect } = require("@playwright/test");

const ONE_PIXEL_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

test("provider completes onboarding on mobile without staff edits", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });

  await page.goto("/palvelut/account/login/");
  await page.getByLabel("Username").fill("provider-e2e@example.test");
  await page.getByLabel("Password").fill("provider-e2e-pass");
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.goto("/palvelut/account/provider/");
  await expect(page.getByRole("heading", { name: "Provider workspace" })).toBeVisible();
  await page.getByRole("link", { name: "Edit profile" }).click();

  await expect(page.getByText("Complete the profile yourself")).toBeVisible();
  await page.getByLabel("Display name").fill("Synthetic Mobile Legal Specialist");
  await page.getByLabel("Service title").fill("Legal consultation");
  await page.getByLabel("Service description").fill("Synthetic browser acceptance profile.");
  await page.getByLabel("Price text").fill("From 80 EUR");
  await page.getByRole("button", { name: "Save draft" }).click();

  await page.locator("#provider-image").setInputFiles({
    name: "profile.png",
    mimeType: "image/png",
    buffer: ONE_PIXEL_PNG,
  });
  await page.locator("#provider-image-alt").fill("Synthetic profile image");
  await page.getByRole("button", { name: "Upload image" }).click();
  await expect(page.getByText("Synthetic profile image")).toBeVisible();

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(hasHorizontalOverflow).toBe(false);

  await page.getByRole("link", { name: "Preview profile" }).click();
  await expect(page.getByRole("heading", { name: "Synthetic Mobile Legal Specialist" })).toBeVisible();
  await page.getByRole("button", { name: "Submit for review" }).click();

  await expect(page).toHaveURL(/\/palvelut\/account\/provider\/\?submitted=1$/);
  await expect(page.getByRole("status")).toHaveText("Profile submitted for review.");
  await expect(page.getByText("Revision: Pending")).toBeVisible();
});
