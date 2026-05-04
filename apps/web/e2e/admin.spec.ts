import { test, expect, type Page } from "@playwright/test";

/**
 * U7 Step 41: Admin smoke E2E.
 *
 * Prerequisites (NOT enforced by the test runner):
 *   1. The Supabase test user `tanaka@test.works-logue.com` exists.
 *   2. The corresponding `users` row has been promoted to admin via the SQL
 *      from `docs/operations.md` (`UPDATE users SET role='admin' WHERE auth_id=...`).
 *   3. A second test user (suzuki@) is regular (no role mutation).
 *
 * The smoke covers READ paths only — no destructive operations (delete / BAN /
 * real PATCH) because the test environment is shared with the public-data
 * smoke fixtures; mutation tests live as repository / router tests under
 * `apps/api/app/tests/`.
 */

const SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL || "http://localhost:54321";
const ADMIN_EMAIL = "tanaka@test.works-logue.com";
const REGULAR_EMAIL = "suzuki@test.works-logue.com";
const TEST_PASSWORD = "TestPass123!";

async function loginAs(page: Page, email: string) {
  const res = await page.request.post(
    `${SUPABASE_URL}/auth/v1/token?grant_type=password`,
    {
      headers: {
        apikey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "",
        "Content-Type": "application/json",
      },
      data: { email, password: TEST_PASSWORD },
    },
  );
  if (!res.ok()) {
    throw new Error(`Login failed for ${email}: ${res.status()}`);
  }
  const session = await res.json();
  await page.goto("/");
  await page.evaluate(
    (s) => {
      const storageKey = `sb-${new URL(s.url).hostname.split(".")[0]}-auth-token`;
      localStorage.setItem(
        storageKey,
        JSON.stringify({
          access_token: s.access_token,
          refresh_token: s.refresh_token,
          expires_at: Math.floor(Date.now() / 1000) + s.expires_in,
          token_type: "bearer",
          user: s.user,
        }),
      );
    },
    { ...session, url: SUPABASE_URL },
  );
  await page.reload();
  await page.waitForLoadState("networkidle");
}

test.describe("Admin smoke (U7)", () => {
  test("regular user accessing /admin sees a 404 page", async ({ page }) => {
    await loginAs(page, REGULAR_EMAIL);
    const resp = await page.goto("/admin");
    // Next.js notFound() renders the not-found page with status 404.
    expect(resp?.status()).toBe(404);
  });

  test("admin user sees the dashboard with 4 stat cards", async ({ page }) => {
    await loginAs(page, ADMIN_EMAIL);
    await page.goto("/admin");
    await expect(
      page.locator('[data-testid="admin-stats-card-total_users"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="admin-stats-card-total_planters"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="admin-stats-card-new_planters_today"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="admin-stats-card-pending_louge_count"]'),
    ).toBeVisible();
  });

  test("admin can search & filter users", async ({ page }) => {
    await loginAs(page, ADMIN_EMAIL);
    await page.goto("/admin/users");

    const search = page.locator('[data-testid="admin-users-search-input"]');
    await expect(search).toBeVisible();
    await search.fill("test");

    // Toggle filter chips — UI should respond (active chip rerendered).
    await page.locator('[data-testid="filter-chip-banned"]').click();
    await page.locator('[data-testid="filter-chip-all"]').click();
  });

  test("admin can switch planter filters between archived / deleted", async ({
    page,
  }) => {
    await loginAs(page, ADMIN_EMAIL);
    await page.goto("/admin/planters");
    await page.locator('[data-testid="filter-chip-archived"]').click();
    await page.locator('[data-testid="filter-chip-deleted"]').click();
    await page.locator('[data-testid="filter-chip-all"]').click();
  });

  test("admin can open and close the SeedType description editor", async ({
    page,
  }) => {
    await loginAs(page, ADMIN_EMAIL);
    await page.goto("/admin/seed-types");
    // Open the first row's edit dialog.
    const firstEdit = page.locator('[data-testid^="admin-seed-types-edit-"]').first();
    await firstEdit.click();
    await expect(
      page.locator('[data-testid="admin-edit-description-dialog-textarea"]'),
    ).toBeVisible();
    // Close without saving (Esc).
    await page.keyboard.press("Escape");
    await expect(
      page.locator('[data-testid="admin-edit-description-dialog-textarea"]'),
    ).toHaveCount(0);
  });
});
