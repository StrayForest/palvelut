const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./e2e",
  workers: 1,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://nginx:8080",
    browserName: "chromium",
    headless: true,
  },
});
