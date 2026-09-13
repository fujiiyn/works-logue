import { test, expect, type Page } from "@playwright/test";

/**
 * 右カラムは xl(1280px) 未満で display:none になる。setContent の placement で
 * 本文のどこにインライン展開するかが決まる仕組みを守るテスト。
 *
 * 実データ（Seed / Logue / ユーザー）が要るため、フィードが空の環境ではスキップする。
 */

const MOBILE = { width: 390, height: 844 };
const DESKTOP = { width: 1440, height: 900 };

async function firstPlanterHref(page: Page): Promise<string | null> {
  await page.goto("/");
  // フィードは非同期取得。カードか空状態のどちらかが出るまで待ってから判定する
  await page
    .getByTestId("planter-card")
    .first()
    .or(page.getByTestId("planter-feed-empty-cta"))
    .waitFor({ timeout: 20000 });
  if ((await page.getByTestId("planter-card").count()) === 0) return null;
  // カード全体を覆うオーバーレイリンクが /p/{id} を持つ
  return page
    .getByTestId("planter-card")
    .first()
    .locator('a[href^="/p/"]')
    .first()
    .getAttribute("href");
}

/** a が b より DOM 順で前にあるか */
async function isBefore(page: Page, a: string, b: string): Promise<boolean> {
  return page.evaluate(
    ([aSel, bSel]) => {
      const first = document.querySelector(`[data-testid="${aSel}"]`);
      const second = document.querySelector(`[data-testid="${bSel}"]`);
      if (!first || !second) throw new Error(`missing: ${aSel} / ${bSel}`);
      return Boolean(
        first.compareDocumentPosition(second) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      );
    },
    [a, b],
  );
}

test.describe("Right sidebar placement on mobile", () => {
  test.use({ viewport: MOBILE });

  test("planter detail injects its sidebar card into the article body", async ({
    page,
  }) => {
    const href = await firstPlanterHref(page);
    test.skip(!href, "フィードが空（テストデータ未投入）");

    await page.goto(href!);
    await expect(page.getByTestId("planter-detail-title")).toBeVisible();

    const isLogue = (await page.getByTestId("contributors-sidebar").count()) > 0;

    if (isLogue) {
      // 貢献者・フォロー・コピーは本文末尾（bottom）
      const inline = page.getByTestId("right-sidebar-inline-bottom");
      await expect(inline).toBeVisible();
      await expect(inline.getByTestId("contributors-sidebar")).toBeVisible();
      expect(
        await isBefore(page, "planter-detail-title", "contributors-sidebar"),
      ).toBe(true);
    } else {
      // 開花スコアは本文冒頭（top）
      const inline = page.getByTestId("right-sidebar-inline-top");
      await expect(inline).toBeVisible();
      await expect(inline.getByTestId("score-card")).toBeVisible();
      expect(
        await isBefore(page, "score-card", "planter-detail-title"),
      ).toBe(true);
    }

    // 右カラムとインラインで二重にマウントされていないこと
    await expect(
      page.getByTestId(isLogue ? "contributors-sidebar" : "score-card"),
    ).toHaveCount(1);
  });
});

test.describe("Right sidebar placement on desktop", () => {
  test.use({ viewport: DESKTOP });

  test("planter detail keeps its card in the right column only", async ({
    page,
  }) => {
    const href = await firstPlanterHref(page);
    test.skip(!href, "フィードが空（テストデータ未投入）");

    await page.goto(href!);
    await expect(page.getByTestId("planter-detail-title")).toBeVisible();

    // setContent はページ側の useEffect で走るので、auto-retry する toHaveCount で待つ
    const injected = page
      .getByTestId("right-sidebar")
      .getByTestId(/^(score-card|contributors-sidebar)$/);
    await expect(injected).toHaveCount(1);

    await expect(page.getByTestId("right-sidebar-inline-top")).toHaveCount(0);
    await expect(page.getByTestId("right-sidebar-inline-bottom")).toHaveCount(0);
  });
});
