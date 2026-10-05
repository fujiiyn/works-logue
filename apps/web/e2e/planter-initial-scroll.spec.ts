import { test, expect, type Page } from "@playwright/test";

// Initial scroll position of the planter detail page.
// - Logue view: opens at the top so the article is read from its title.
// - Seed view: jumps to the latest log (chat-UI behavior).
//
// Needs real planters with logs, passed by ID:
//   E2E_LOGUE_PLANTER_ID  a bloomed planter (status=logue) with several logs
//   E2E_SEED_PLANTER_ID   a seed planter with at least one log
// Each test is skipped when its ID is not set.

const LOGUE_ID = process.env.E2E_LOGUE_PLANTER_ID;
const SEED_ID = process.env.E2E_SEED_PLANTER_ID;

// A short viewport makes both pages taller than the window, so the scroll
// position actually tells the two behaviors apart.
test.use({ viewport: { width: 390, height: 600 } });

async function openAndWaitForLogs(page: Page, planterId: string) {
  // Opening the page POSTs a view record. Answer it here so the test never
  // writes to the database it reads from.
  await page.route("**/api/v1/planters/*/view", (route) =>
    route.fulfill({ status: 204 }),
  );
  await page.goto(`/p/${planterId}`);
  await expect(page.getByTestId("log-item").first()).toBeVisible({
    timeout: 20000,
  });
  // The initial jump runs in a layout effect plus one animation frame.
  await page.evaluate(
    () => new Promise((r) => requestAnimationFrame(() => setTimeout(r, 300))),
  );
}

async function scrollState(page: Page) {
  return page.evaluate(() => ({
    scrollY: window.scrollY,
    scrollable:
      document.documentElement.scrollHeight - window.innerHeight,
  }));
}

test("Logue page opens at the top, not scrolled to the latest log", async ({
  page,
}) => {
  test.skip(!LOGUE_ID, "E2E_LOGUE_PLANTER_ID is not set");
  await openAndWaitForLogs(page, LOGUE_ID!);

  const { scrollY, scrollable } = await scrollState(page);
  // Canary: on a page that can't scroll, scrollY is always 0 and the
  // assertion below would pass even with the bug.
  expect(scrollable).toBeGreaterThan(200);
  expect(scrollY).toBe(0);
  await expect(page.getByTestId("planter-detail-title")).toBeInViewport();
});

test("Seed page still jumps to the latest log", async ({ page }) => {
  test.skip(!SEED_ID, "E2E_SEED_PLANTER_ID is not set");
  await openAndWaitForLogs(page, SEED_ID!);

  const { scrollY, scrollable } = await scrollState(page);
  expect(scrollable).toBeGreaterThan(0);
  expect(scrollY).toBeGreaterThan(0);
});
