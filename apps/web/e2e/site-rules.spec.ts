import { test, expect } from "@playwright/test";

test.use({ viewport: { width: 1440, height: 900 } });

test.describe("Site rules pages", () => {
  test("home footer links navigate to privacy policy", async ({ page }) => {
    await page.goto("/");
    const footer = page.getByTestId("site-rules-footer");
    await expect(footer).toBeVisible();
    await footer.getByRole("link", { name: "プライバシーポリシー" }).click();
    await expect(page).toHaveURL("/rules/privacy-policy");
    await expect(
      page.getByRole("heading", { name: "プライバシーポリシー", level: 1 }),
    ).toBeVisible();
    await expect(page.getByTestId("markdown-document")).toBeVisible();
  });

  test("terms of service page renders", async ({ page }) => {
    await page.goto("/rules/terms-of-service");
    await expect(
      page.getByRole("heading", { name: "利用規約", level: 1 }),
    ).toBeVisible();
    await expect(page.getByTestId("markdown-document")).toBeVisible();
  });

  test("contents policy page renders", async ({ page }) => {
    await page.goto("/rules/contents-policy");
    await expect(
      page.getByRole("heading", { name: "コンテンツポリシー", level: 1 }),
    ).toBeVisible();
    await expect(page.getByTestId("markdown-document")).toBeVisible();
  });

  test("unknown rules slug shows not-found", async ({ page }) => {
    const response = await page.goto("/rules/unknown");
    expect(response?.status()).toBe(404);
    await expect(
      page.getByRole("heading", { name: "ページが見つかりません", level: 1 }),
    ).toBeVisible();
  });
});
