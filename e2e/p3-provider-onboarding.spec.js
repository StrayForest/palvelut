const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

const ONE_PIXEL_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);
const P6_WIDTHS = [360, 390, 768, 1024, 1440];
const P6_EVIDENCE_DIR = path.join("test-results", "p6-provider-readiness-evidence");

async function saveP6Evidence(page, testInfo, name, width) {
  await page.setViewportSize({ width, height: 900 });
  const hasOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  );
  expect(hasOverflow).toBe(false);

  fs.mkdirSync(P6_EVIDENCE_DIR, { recursive: true });
  const filename = `${name}-${width}.png`;
  const screenshotPath = path.join(P6_EVIDENCE_DIR, filename);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach(filename, { path: screenshotPath, contentType: "image/png" });
}

test("provider completes onboarding on mobile without staff edits", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 360, height: 800 });

  await page.goto("/palvelut/account/login/");
  await page.getByLabel("Электронная почта").fill("provider-e2e@example.test");
  await page.getByLabel("Пароль").fill("provider-e2e-pass");
  await page.getByRole("button", { name: "Войти" }).click();

  await page.goto("/palvelut/account/profile/");
  await expect(page.getByRole("heading", { name: "Кабинет специалиста" })).toBeVisible();
  await page.getByRole("link", { name: "Продолжить заполнение" }).click();

  await expect(page.getByRole("heading", { level: 1, name: /Редактировать/ })).toBeVisible();
  for (const width of P6_WIDTHS) {
    await saveP6Evidence(page, testInfo, "workspace-edit", width);
  }
  await page.setViewportSize({ width: 360, height: 800 });

  await page.getByLabel("Название в каталоге").fill("Synthetic Mobile Legal Specialist");
  await page.getByLabel("Название услуги").fill("Legal consultation");
  await page.getByLabel("Описание услуги").fill("Synthetic browser acceptance profile.");
  await page.getByLabel("Цена или принцип расчёта").fill("From 80 EUR");
  await page.getByRole("button", { name: "Сохранить черновик" }).click();

  await page.locator("#provider-image").setInputFiles({
    name: "profile.png",
    mimeType: "image/png",
    buffer: ONE_PIXEL_PNG,
  });
  await page.locator("#provider-image-alt").fill("Synthetic profile image");
  await page.getByRole("button", { name: "Загрузить изображение" }).click();
  await expect(page.getByText("Synthetic profile image")).toBeVisible();

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(hasHorizontalOverflow).toBe(false);

  await page.getByRole("link", { name: "Посмотреть предпросмотр" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Предпросмотр карточки" })).toBeVisible();
  await expect(page.getByText("Synthetic Mobile Legal Specialist", { exact: true })).toBeVisible();
  for (const width of P6_WIDTHS) {
    await saveP6Evidence(page, testInfo, "workspace-preview", width);
  }
  await page.setViewportSize({ width: 360, height: 800 });
  await page.getByRole("button", { name: "Отправить на проверку" }).click();

  await expect(page).toHaveURL(/\/palvelut\/account\/profile\/\?submitted=1$/);
  await expect(page.getByRole("status")).toHaveText("Карточка отправлена на проверку.");
  await expect(page.getByText("Карточка на проверке.")).toBeVisible();
});

test("provider pending workspace has keyboard and accessibility smoke coverage", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/palvelut/account/login/");
  await page.getByLabel("Электронная почта").fill("provider-e2e@example.test");
  await page.getByLabel("Пароль").fill("provider-e2e-pass");
  await page.getByRole("button", { name: "Войти" }).click();

  await page.goto("/palvelut/account/profile/");
  await expect(page.getByRole("heading", { level: 1, name: "Кабинет специалиста" })).toBeVisible();
  await expect(page.getByText("Карточка на проверке.")).toBeVisible();
  await expect(page.getByText("Дождитесь проверки. Последняя версия карточки уже отправлена на модерацию.")).toBeVisible();

  const startAnother = page.getByRole("link", { name: "Создать ещё одну карточку" });
  await startAnother.focus();
  await expect(startAnother).toBeFocused();

  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((violation) =>
    ["serious", "critical"].includes(violation.impact),
  );
  expect(blocking, blocking.map((item) => item.id).join(", ")).toEqual([]);
});
