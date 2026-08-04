import { test, expect } from "@playwright/test";

test.use({ viewport: { width: 1440, height: 900 } });

const HERO_HEADING = "「技術ブログ」がないのだろう";

test.describe("About LP", () => {
  test("footer link navigates from home to the LP", async ({ page }) => {
    await page.goto("/");
    const footer = page.getByTestId("site-rules-footer");
    await expect(footer).toBeVisible();
    await footer.getByRole("link", { name: "Works Logue とは" }).click();
    // dev サーバーでは遷移先の初回コンパイルを待つため長めに取る
    await expect(page).toHaveURL("/about", { timeout: 20000 });
    await expect(page.getByRole("heading", { level: 1 })).toContainText(
      HERO_HEADING,
    );
  });

  test("LP renders standalone without the app chrome", async ({ page }) => {
    await page.goto("/about");
    await expect(page.getByTestId("about-lp")).toBeVisible();
    await expect(page.getByTestId("header")).toHaveCount(0);
    await expect(page.getByTestId("sidebar")).toHaveCount(0);
    await expect(page.getByTestId("right-sidebar")).toHaveCount(0);
  });

  test("all sections and the Seed-to-Logue cycle are shown", async ({
    page,
  }) => {
    await page.goto("/about");
    await expect(page.getByTestId("about-hero")).toBeVisible();

    for (const heading of [
      "エンジニアの文化に惹かれ、違和感を覚えた",
      "生成AIには、絶対に作れないもの",
      "種から花へ。Works Logue の仕組み",
      "これから一緒に実現したいこと",
    ]) {
      await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    }

    // 円環（デスクトップ）と縦並び（モバイル）で同じ段階を出すため first() を見る
    const cycle = page.getByTestId("about-cycle");
    await cycle.scrollIntoViewIfNeeded();
    for (const stage of ["Seed", "Log", "Logic", "Logue", "Fork"]) {
      await expect(
        cycle.locator(`[data-stage="${stage}"]`).first(),
      ).toBeVisible();
    }
  });

  test("closing CTA leads to the home feed", async ({ page }) => {
    await page.goto("/about");
    const cta = page.getByTestId("about-cta-start");
    await cta.scrollIntoViewIfNeeded();
    await expect(cta).toHaveText("Works Logue を始める");
    await cta.click();
    await expect(page).toHaveURL("/", { timeout: 20000 });
  });
});
