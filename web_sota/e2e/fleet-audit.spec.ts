import { expect, test } from "@playwright/test";

const BE = "http://127.0.0.1:10907";

test.describe("Fleet Audit", () => {
  test("Backend health", async ({ request }) => {
    const resp = await request.get(`${BE}/health`);
    expect(resp.status()).toBe(200);
  });

  test("Backend status + tools", async ({ request }) => {
    const resp = await request.get(`${BE}/api/status`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.status).toBe("ok");
    expect(body.tool_count).toBeGreaterThanOrEqual(12);
  });

  test("Frontend loads", async ({ page }) => {
    await page.goto("/", { timeout: 15000 });
    await expect(page.locator("#root")).toBeAttached();
    await expect(page.getByTestId("dashboard")).toBeAttached();
  });

  test("Dashboard shows backend KPIs", async ({ page }) => {
    await page.goto("/", { timeout: 15000 });
    await expect(page.getByTestId("kpi-tools")).toContainText(/\d+/);
  });

  test("No console errors on navigation", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    page.on("pageerror", (err) => errors.push(err.message));
    await page.goto("/", { timeout: 15000 });
    await page.goto("/notebooks", { timeout: 15000 });
    await page.goto("/chat", { timeout: 15000 });
    await page.goto("/help", { timeout: 15000 });
    expect(errors).toEqual([]);
  });
});
