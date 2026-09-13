import { test, expect } from "@playwright/test";

const MOBILE = { width: 390, height: 844 };
const DESKTOP = { width: 1440, height: 900 };

test.describe("Mobile layout (< xl)", () => {
  test.use({ viewport: MOBILE });

  test("header keeps the Works Logue wordmark and hides Seed when logged out", async ({
    page,
  }) => {
    await page.goto("/");

    const wordmark = page.getByTestId("header-logo").getByText("Works Logue");
    await expect(wordmark).toBeVisible();
    // 省略記号で潰れていないこと。
    // この span は header-logo（flex コンテナ）の flex item なので実幅を持つ。
    // flex を外すと両方 0 になり素通りするため、canary で幅を確認してから比較する。
    const { scrollWidth, clientWidth } = await wordmark.evaluate((el) => ({
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
    }));
    expect(scrollWidth).toBeGreaterThan(0);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);

    await expect(page.getByTestId("header-login-button")).toBeVisible();
    await expect(page.getByTestId("header-seed-button")).toHaveCount(0);
  });

  test("site rules links are reachable from the hamburger drawer", async ({
    page,
  }) => {
    await page.goto("/");

    // xl 未満では右カラムが display:none。規約リンクはドロワー側にある
    await expect(page.getByTestId("site-rules-footer")).not.toBeVisible();

    await page.getByTestId("header-hamburger").click();
    const drawerFooter = page.getByTestId("site-rules-footer-drawer");
    await expect(drawerFooter).toBeVisible();

    await drawerFooter.getByRole("link", { name: "利用規約" }).click();
    await expect(page).toHaveURL("/rules/terms-of-service", { timeout: 20000 });
  });

  test("main content is not clipped horizontally", async ({ page }) => {
    await page.goto("/");
    const overflow = await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });
});

test.describe("Tablet layout (md - xl)", () => {
  // 768-1279px は左ナビが出て右カラムが消える唯一の帯。
  // 規約リンクは左ナビ下部（site-rules-footer-nav）にだけ現れる。
  test.use({ viewport: { width: 1024, height: 768 } });

  test("left nav carries the site rules links while the right column is gone", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(page.getByTestId("sidebar")).toBeVisible();
    await expect(page.getByTestId("right-sidebar")).not.toBeVisible();

    const navFooter = page.getByTestId("site-rules-footer-nav");
    await expect(navFooter).toBeVisible();
    await expect(page.getByTestId("site-rules-footer")).not.toBeVisible();

    await navFooter.getByRole("link", { name: "コンテンツポリシー" }).click();
    await expect(page).toHaveURL("/rules/contents-policy", { timeout: 20000 });
  });
});

test.describe("Desktop layout (xl+)", () => {
  test.use({ viewport: DESKTOP });

  test("right column renders and no inline fallback is mounted", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(page.getByTestId("right-sidebar")).toBeVisible();
    await expect(page.getByTestId("about-card")).toBeVisible();
    await expect(page.getByTestId("site-rules-footer")).toBeVisible();

    // 右カラムとインラインの二重マウントが起きていないこと
    await expect(page.getByTestId("right-sidebar-inline-top")).toHaveCount(0);
    await expect(page.getByTestId("right-sidebar-inline-bottom")).toHaveCount(0);
    // ドロワー用フッターはこの幅では出さない
    await expect(page.getByTestId("site-rules-footer-drawer")).toHaveCount(0);
  });
});
