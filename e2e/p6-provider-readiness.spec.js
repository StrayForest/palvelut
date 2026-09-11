const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const widths = [360, 390, 768, 1024, 1440];
const evidenceDir = path.join("test-results", "p6-provider-readiness-evidence");
const TEST_EMAIL = "provider-fresh-e2e@example.test";
const TEST_PASSWORD = "provider-fresh-e2e-pass"; // test-only synthetic fixture

async function saveEvidence(page, testInfo, name, width) {
  await page.setViewportSize({ width, height: 900 });
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

async function capture(page, testInfo, name, url, width) {
  await page.setViewportSize({ width, height: 900 });
  const response = await page.goto(url);
  expect(response).not.toBeNull();
  expect(response.status()).toBe(200);
  await saveEvidence(page, testInfo, name, width);
}

test("Russian-only public provider entry and registration are usable", async ({ page }, testInfo) => {
  test.setTimeout(300_000);

  for (const unsupported of ["/palvelut/en/", "/palvelut/fi/", "/palvelut/en/legal/privacy/"]) {
    const response = await page.goto(unsupported);
    expect(response).not.toBeNull();
    expect(response.status()).toBe(404);
  }

  for (const width of widths) {
    await capture(page, testInfo, "public-provider-cta", "/palvelut/ru/", width);
    await expect(page.getByRole("link", { name: "Разместить карточку" }).first()).toBeVisible();
    await capture(page, testInfo, "for-professionals", "/palvelut/ru/for-professionals/", width);
    await capture(page, testInfo, "provider-terms", "/palvelut/ru/legal/terms/", width);
    await capture(page, testInfo, "privacy-notice", "/palvelut/ru/legal/privacy/", width);
    await capture(page, testInfo, "register", "/palvelut/account/register/", width);
    await capture(page, testInfo, "login", "/palvelut/account/login/", width);
  }

  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/palvelut/account/register/");
  const email = page.locator('input[name="email"]');
  await email.focus();
  await expect(email).toBeFocused();
  for (const width of widths) {
    await saveEvidence(page, testInfo, "register-focus", width);
  }

  const registrationEmail = `browser-registration-${Date.now()}@example.test`;
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/palvelut/account/register/");
  await page.locator('input[name="email"]').fill(registrationEmail);
  await page.locator('input[name="password1"]').fill("Browser-registration-pass-2026!");
  await page.locator('input[name="password2"]').fill("Browser-registration-pass-2026!");
  await page.getByRole("button", { name: "Создать аккаунт" }).click();
  await expect(page.getByRole("heading", { name: "Проверьте электронную почту" })).toBeVisible();
  await expect(page.getByText("Мы отправили ссылку для подтверждения.")).toBeVisible();
  for (const width of widths) {
    await saveEvidence(page, testInfo, "registration-submitted", width);
  }
});

test("brand-new confirmed provider can enter self-service without preseeded provider or membership", async ({ page }, testInfo) => {
  test.setTimeout(300_000);

  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/palvelut/account/login/");
  await page.locator('input[name="username"]').fill(TEST_EMAIL);
  await page.locator('input[name="password"]').fill("not-a-real-password");
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page.locator(".errorlist").first()).toBeVisible();
  for (const width of widths) {
    await saveEvidence(page, testInfo, "login-errors", width);
  }

  await page.setViewportSize({ width: 390, height: 900 });
  await page.locator('input[name="username"]').fill(TEST_EMAIL);
  await page.locator('input[name="password"]').fill(TEST_PASSWORD);
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page).toHaveURL(/\/palvelut\/account\/profile\/$/);
  await expect(page.locator("#workspace-empty-state")).toBeVisible();
  await expect(page.getByRole("link", { name: "Создать новую карточку" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Подтвердить существующую" })).toBeVisible();

  for (const width of widths) {
    await capture(page, testInfo, "workspace-empty", "/palvelut/account/profile/", width);
    await capture(page, testInfo, "provider-start", "/palvelut/account/provider/start/", width);
  }

  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/palvelut/account/provider/start/");
  await page.locator('select[name="provider_type"]').selectOption("individual");
  await page.locator('input[name="legal_name"]').fill("Fresh Browser Professional");
  await page.locator('input[name="display_name"]').fill("Fresh Browser Professional");
  await page.locator('select[name="evidence_kind"]').selectOption("staff_reviewed_equivalent");
  await page.locator('textarea[name="evidence_reference"]').fill("Synthetic staff-reviewed ownership evidence");
  await page.locator('input[name="provider_terms_accepted"]').check();
  await page.getByRole("button", { name: "Отправить данные на проверку" }).click();
  await expect(page.getByText("Нужно подтверждение профессионального права в официальном источнике.")).toBeVisible();
  await expect(page.getByText("Нужно подтверждение работодателя.")).toBeVisible();
  const professionalRight = page.locator('input[name="professional_right_reference"]');
  await professionalRight.focus();
  await expect(professionalRight).toBeFocused();
  for (const width of widths) {
    await saveEvidence(page, testInfo, "provider-start-errors", width);
  }

  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/palvelut/account/provider/start/");
  await expect(page.getByRole("link", { name: "Прочитать условия" })).toBeVisible();
  await page.locator('select[name="provider_type"]').selectOption("business");
  await page.locator('input[name="legal_name"]').fill("Fresh Browser Provider Oy");
  await page.locator('input[name="display_name"]').fill("Fresh Browser Provider");
  await page.locator('input[name="y_tunnus"]').fill("1357924-6");
  await page.locator('select[name="evidence_kind"]').selectOption("registry_signatory");
  await page.locator('textarea[name="evidence_reference"]').fill("Synthetic PRH signatory evidence for browser acceptance");
  await page.locator('input[name="provider_terms_accepted"]').check();
  await page.getByRole("button", { name: "Отправить данные на проверку" }).click();

  await expect(page).toHaveURL(/\/palvelut\/account\/profile\/$/);
  await expect(page.getByText("Fresh Browser Provider")).toBeVisible();
  await expect(page.getByText("Подтверждение отправлено на проверку.")).toBeVisible();
  await expect(page.getByText(/Карточка пока не опубликована/)).toBeVisible();

  for (const width of widths) {
    await capture(page, testInfo, "ownership-pending", "/palvelut/account/profile/", width);
  }
});

test("public report policy surface is retained in Russian across supported widths", async ({ page }, testInfo) => {
  test.setTimeout(120_000);
  await page.goto("/palvelut/ru/search/?q=accounting");
  await page.getByRole("link", { name: "Открыть карточку" }).first().click();
  await page.getByRole("link", { name: "Сообщить о проблеме в карточке" }).click();
  await expect(page.getByText("Что произойдёт дальше")).toBeVisible();
  await expect(page.getByText(/Жалоба не удаляет карточку автоматически/)).toBeVisible();

  for (const width of widths) {
    await saveEvidence(page, testInfo, "content-report-policy", width);
  }
});
