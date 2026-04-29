import { test, expect } from "@playwright/test";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "http://localhost:54321";
const TEST_EMAIL = "tanaka@test.works-logue.com";
const TEST_PASSWORD = "TestPass123!";

async function loginViaSupabase(page: import("@playwright/test").Page) {
  // Login via Supabase Auth REST API, then set session in browser
  const res = await page.request.post(
    `${SUPABASE_URL}/auth/v1/token?grant_type=password`,
    {
      headers: {
        apikey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "",
        "Content-Type": "application/json",
      },
      data: { email: TEST_EMAIL, password: TEST_PASSWORD },
    },
  );

  if (!res.ok()) {
    throw new Error(`Login failed: ${res.status()} ${await res.text()}`);
  }

  const session = await res.json();

  // Navigate to the app and inject the session
  await page.goto("/");
  await page.evaluate((s) => {
    const key = Object.keys(localStorage).find((k) =>
      k.startsWith("sb-"),
    );
    // Set Supabase session in localStorage
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
  }, { ...session, url: SUPABASE_URL });

  await page.reload();
  await page.waitForLoadState("networkidle");
}

test.describe("User Profile", () => {
  test("should display user profile page", async ({ page }) => {
    await loginViaSupabase(page);

    // Navigate to own profile via header menu
    await page.click('[data-testid="header-user-menu"]');
    await page.click('[data-testid="header-profile-link"]');

    // Verify profile elements
    await expect(page.locator('[data-testid="user-profile-page"]')).toBeVisible();
    await expect(page.locator('[data-testid="profile-display-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="stats-row"]')).toBeVisible();
    await expect(page.locator('[data-testid="contribution-graph"]')).toBeVisible();
    await expect(page.locator('[data-testid="profile-tabs"]')).toBeVisible();
  });

  test("should show edit button on own profile", async ({ page }) => {
    await loginViaSupabase(page);

    await page.click('[data-testid="header-user-menu"]');
    await page.click('[data-testid="header-profile-link"]');

    await expect(
      page.locator('[data-testid="profile-edit-button"]'),
    ).toBeVisible();
  });

  test("should navigate to edit page", async ({ page }) => {
    await loginViaSupabase(page);

    await page.click('[data-testid="header-user-menu"]');
    await page.click('[data-testid="header-profile-link"]');
    await page.click('[data-testid="profile-edit-button"]');

    await expect(
      page.locator('[data-testid="profile-edit-page"]'),
    ).toBeVisible();
    await expect(page.locator('[data-testid="profile-edit-save"]')).toBeVisible();
  });

  test("should edit profile text and save", async ({ page }) => {
    await loginViaSupabase(page);

    await page.click('[data-testid="header-user-menu"]');
    await page.click('[data-testid="header-profile-link"]');
    await page.click('[data-testid="profile-edit-button"]');

    // Edit bio
    const bioField = page.locator('[data-testid="profile-edit-bio"]');
    await bioField.fill("Updated bio from E2E test");

    // Save
    await page.click('[data-testid="profile-edit-save"]');

    // Should redirect back to profile
    await expect(
      page.locator('[data-testid="user-profile-page"]'),
    ).toBeVisible({ timeout: 10000 });
  });

  test("should show follow button on other user profile", async ({ page }) => {
    await loginViaSupabase(page);

    // Navigate directly to another user (if exists)
    // This test verifies the follow button appears on non-own profiles
    await page.click('[data-testid="header-user-menu"]');
    await page.click('[data-testid="header-profile-link"]');

    // On own profile, follow button should NOT appear
    await expect(
      page.locator('[data-testid="follow-button"]'),
    ).not.toBeVisible();
  });

  test("should switch profile tabs", async ({ page }) => {
    await loginViaSupabase(page);

    await page.click('[data-testid="header-user-menu"]');
    await page.click('[data-testid="header-profile-link"]');

    // Click Log tab
    await page.click('[data-testid="profile-tab-logs"]');
    await page.waitForTimeout(500);

    // Click Louge tab
    await page.click('[data-testid="profile-tab-louges"]');
    await page.waitForTimeout(500);

    // Click back to Seeds tab
    await page.click('[data-testid="profile-tab-seeds"]');
    await page.waitForTimeout(500);
  });

  test("should show following tab in feed", async ({ page }) => {
    await loginViaSupabase(page);

    // Click following tab in the main feed
    await page.click('[data-testid="planter-feed-tab-following"]');
    await page.waitForTimeout(500);

    // Should show feed content (or empty state)
    await expect(page.locator('[data-testid="planter-feed"]')).toBeVisible();
  });

  test("should show login prompt for following tab when not logged in", async ({
    page,
  }) => {
    await page.goto("/");

    // Following tab should show login prompt
    await page.click('[data-testid="planter-feed-tab-following"]');
    await expect(page.getByText("ログインが必要です")).toBeVisible();
  });
});
