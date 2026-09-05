const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

const smokeRoutes = [
  "/palvelut/en/",
  "/palvelut/en/search/",
  "/palvelut/en/trust/",
  "/palvelut/en/legal/privacy/",
];

for (const route of smokeRoutes) {
  test(`${route} exposes screen-reader-facing semantics without serious axe findings`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response).not.toBeNull();
    expect(response.status()).toBe(200);

    await expect(page.getByRole("main")).toHaveCount(1);
    await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);

    const accessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();
    const blockingViolations = accessibility.violations.filter((violation) =>
      ["critical", "serious"].includes(violation.impact),
    );
    expect(blockingViolations).toEqual([]);
  });
}

test("keyboard smoke follows the public search form in DOM order", async ({ page }) => {
  await page.goto("/palvelut/en/");

  const service = page.getByRole("textbox", { name: "What service?" });
  const city = page.getByRole("combobox", { name: "Where?" });
  const search = page.getByRole("button", { name: "Search" });

  await service.focus();
  await expect(service).toBeFocused();

  await page.keyboard.press("Tab");
  await expect(city).toBeFocused();

  await page.keyboard.press("Tab");
  await expect(search).toBeFocused();

  await service.fill("accountant");
  await city.selectOption({ label: "Helsinki" });
  await search.focus();
  await page.keyboard.press("Enter");

  await expect(page).toHaveURL(/\/palvelut\/en\/search\/\?.*q=accountant/);
  await expect(page.getByRole("main")).toHaveCount(1);
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
});
