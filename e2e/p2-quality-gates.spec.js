const { test, expect, chromium } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

const publicRoutes = [
  "/palvelut/en/",
  "/palvelut/en/search/?q=accounting",
  "/palvelut/en/search/?q=definitely-no-provider",
];

test("P2 public discovery has no serious or critical axe violations", async ({ page }) => {
  for (const route of publicRoutes) {
    const response = await page.goto(route);
    expect(response).not.toBeNull();
    expect(response.status()).toBe(200);
    const results = await new AxeBuilder({ page }).analyze();
    const blocking = results.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact),
    );
    expect(blocking, `${route}: ${blocking.map((item) => item.id).join(", ")}`).toEqual([]);
  }
});

test("P2 cold and warm anonymous discovery smoke stays inside response budgets", async ({ page }) => {
  const route = `/palvelut/en/search/?q=p2-gate-${Date.now()}`;
  const startedCold = Date.now();
  const cold = await page.goto(route);
  const coldMs = Date.now() - startedCold;
  expect(cold).not.toBeNull();
  expect(cold.status()).toBe(200);
  expect(coldMs).toBeLessThanOrEqual(800);

  const startedWarm = Date.now();
  const warm = await page.goto(route);
  const warmMs = Date.now() - startedWarm;
  expect(warm).not.toBeNull();
  expect(warm.status()).toBe(200);
  expect(warmMs).toBeLessThanOrEqual(300);
});

test("P2 home passes Lighthouse performance accessibility and SEO categories", async () => {
  test.setTimeout(120_000);
  const chromeLauncher = await import("chrome-launcher");
  const lighthouseModule = await import("lighthouse");
  const chrome = await chromeLauncher.launch({
    chromePath: chromium.executablePath(),
    chromeFlags: ["--headless", "--no-sandbox", "--disable-dev-shm-usage"],
  });
  try {
    const result = await lighthouseModule.default("http://nginx:8080/palvelut/en/", {
      port: chrome.port,
      logLevel: "error",
      output: "json",
      onlyCategories: ["performance", "accessibility", "seo"],
    });
    expect(result).toBeTruthy();
    const categories = result.lhr.categories;
    expect(categories.performance.score).toBeGreaterThanOrEqual(0.8);
    expect(categories.accessibility.score).toBeGreaterThanOrEqual(0.9);
    expect(categories.seo.score).toBeGreaterThanOrEqual(0.9);
  } finally {
    await chrome.kill();
  }
});
