const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const browserEvidence = new Map();

test.beforeEach(async ({ page }, testInfo) => {
  const evidence = { consoleMessages: [], pageErrors: [] };
  browserEvidence.set(testInfo.testId, evidence);

  page.on("console", (message) => {
    evidence.consoleMessages.push(`[${message.type()}] ${message.text()}`);
  });
  page.on("pageerror", (error) => evidence.pageErrors.push(error.message));
});

test.afterEach(async ({}, testInfo) => {
  const evidence = browserEvidence.get(testInfo.testId);
  if (evidence && testInfo.status !== testInfo.expectedStatus) {
    const outputPath = testInfo.outputPath("console.log");
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    const lines = [
      ...evidence.consoleMessages,
      ...evidence.pageErrors.map((message) => `[pageerror] ${message}`),
    ];
    fs.writeFileSync(outputPath, `${lines.join("\n")}\n`, "utf8");
    await testInfo.attach("console-log", {
      path: outputPath,
      contentType: "text/plain",
    });
  }
  browserEvidence.delete(testInfo.testId);
});

for (const width of [360, 1440]) {
  test(`base page is usable at ${width}px with keyboard focus and no console errors`, async ({ page }, testInfo) => {
    const evidence = browserEvidence.get(testInfo.testId);

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

    expect(evidence.consoleMessages.filter((line) => line.startsWith("[error]"))).toEqual([]);
    expect(evidence.pageErrors).toEqual([]);
  });
}

test("discovery filters work without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();

  const response = await page.goto("/palvelut/en/search/?q=accounting");
  expect(response).not.toBeNull();
  expect(response.status()).toBe(200);

  const service = page.locator("#discovery-service");
  await expect(service).toHaveValue("accounting");
  await service.fill("bookkeeper");
  await page.getByRole("button", { name: "Apply filters" }).click();

  await expect(page).toHaveURL(/\/palvelut\/en\/search\/\?q=bookkeeper/);
  await expect(page.locator("#discovery-service")).toHaveValue("bookkeeper");
  await context.close();
});

test("HTMX discovery filters preserve URL history and focused field", async ({ page }) => {
  await page.goto("/palvelut/en/search/?q=accounting");

  const service = page.locator("#discovery-service");
  await service.focus();
  await expect(service).toBeFocused();
  await service.fill("bookkeeper");

  await Promise.all([
    page.waitForResponse((response) =>
      response.url().includes("/palvelut/en/search/?q=bookkeeper"),
    ),
    page.getByRole("button", { name: "Apply filters" }).click(),
  ]);

  await expect(page).toHaveURL(/\/palvelut\/en\/search\/\?q=bookkeeper/);
  await expect(page.locator("#discovery-service")).toBeFocused();
  await expect(page.locator("#discovery-service")).toHaveValue("bookkeeper");

  await page.goBack();
  await expect(page).toHaveURL(/\/palvelut\/en\/search\/\?q=accounting/);
  await expect(page.locator("#discovery-service")).toHaveValue("accounting");
});
