const { test, expect } = require("@playwright/test");

const publicRoutes = [
  "/palvelut/en/",
  "/palvelut/en/search/",
  "/palvelut/en/trust/",
  "/palvelut/en/legal/privacy/",
];

for (const route of publicRoutes) {
  test(`${route} exposes a screen-reader-friendly document outline`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response).not.toBeNull();
    expect(response.status()).toBe(200);

    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator("main")).toHaveCount(1);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(
      page.locator('[tabindex]:not([tabindex="0"]):not([tabindex="-1"])'),
    ).toHaveCount(0);

    const unnamedInteractive = await page.locator(
      "a[href], button, input, select, textarea",
    ).evaluateAll((elements) =>
      elements
        .filter((element) => {
          const labelledBy = element.getAttribute("aria-labelledby");
          const labelledByText = labelledBy
            ? labelledBy
                .split(/\s+/)
                .map((id) => document.getElementById(id)?.textContent || "")
                .join(" ")
                .trim()
            : "";
          const id = element.id;
          const labelText = id
            ? Array.from(document.querySelectorAll(`label[for="${CSS.escape(id)}"]`))
                .map((label) => label.textContent || "")
                .join(" ")
                .trim()
            : "";
          const wrappingLabelText = element.closest("label")?.textContent?.trim() || "";
          const text = element.textContent?.trim() || "";
          const ariaLabel = element.getAttribute("aria-label")?.trim() || "";
          const title = element.getAttribute("title")?.trim() || "";
          const alt = element.getAttribute("alt")?.trim() || "";
          const value =
            element instanceof HTMLInputElement &&
            ["button", "submit", "reset"].includes(element.type)
              ? element.value.trim()
              : "";
          return !(
            labelledByText ||
            labelText ||
            wrappingLabelText ||
            text ||
            ariaLabel ||
            title ||
            alt ||
            value
          );
        })
        .map((element) => element.outerHTML),
    );
    expect(unnamedInteractive).toEqual([]);
  });
}

test("keyboard-only navigation reaches the skip link and main content", async ({ page }) => {
  await page.goto("/palvelut/en/");

  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Skip to main content" });
  await expect(skipLink).toBeFocused();

  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();

  await page.keyboard.press("Tab");
  await expect(page.locator("#main-content")).not.toBeFocused();
});

test("public home remains usable at 200 percent text zoom without horizontal clipping", async ({ page }) => {
  await page.setViewportSize({ width: 640, height: 900 });
  await page.goto("/palvelut/en/");
  await page.evaluate(() => {
    document.documentElement.style.fontSize = "200%";
  });

  const dimensions = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
  await expect(page.getByRole("button", { name: "Search" })).toBeVisible();
});

test("reduced-motion preference does not block public navigation", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/palvelut/en/");

  await page.getByRole("link", { name: "Privacy" }).click();
  await expect(page).toHaveURL(/\/palvelut\/en\/legal\/privacy\/$/);
  await expect(page.locator("h1")).toBeVisible();
});
