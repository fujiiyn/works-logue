"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { apiFetch } from "@/lib/api-client";
import { Skeleton } from "@/components/common/Skeleton";
import { TagAccordionSelector } from "@/components/common/TagAccordionSelector";

export default function OnboardingPage() {
  return (
    <Suspense>
      <OnboardingForm />
    </Suspense>
  );
}

function OnboardingForm() {
  const { user, isLoading, refreshUser } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/";

  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || "");
      setBio(user.bio || "");
    }
  }, [user]);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push(`/login?redirect=${encodeURIComponent(`/onboarding?redirect=${redirect}`)}`);
    }
    if (user && user.onboarded_at) {
      router.push(redirect);
    }
  }, [user, isLoading, router, redirect]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!displayName.trim()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await apiFetch("/api/v1/users/me", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: displayName.trim(),
          bio: bio.trim() || null,
          tag_ids: selectedTagIds,
          complete_onboarding: true,
        }),
      });

      // Refresh auth context so onboarded_at is set
      await refreshUser();

      // Validate redirect URL (prevent open redirect)
      const target = redirect.startsWith("/") && !redirect.startsWith("//")
        ? redirect
        : "/";
      router.push(target);
    } catch {
      setError("設定の保存に失敗しました。もう一度お試しください。");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex gap-6">
        <div className="min-w-0 flex-1 space-y-4">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-96" />
          {/* Display name */}
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-[42px] rounded-md" />
          {/* Tags */}
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-4 w-72" />
          <Skeleton className="h-[200px] rounded-md" />
          {/* Bio */}
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-[80px] rounded-md" />
          {/* Button */}
          <div className="flex justify-end">
            <Skeleton className="h-[42px] w-40 rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-6" data-testid="onboarding-page">
      <div className="min-w-0 flex-1">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <h1 className="text-[22px] font-semibold text-primary-dark">
            プロフィールを設定しましょう
          </h1>
          <p className="text-body-m text-text-secondary">
            あなたの専門性を設定することで、より関連性の高い知恵と出会えます。あとから変更することもできます。
          </p>

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body-s text-red-700">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-2">
            <label
              htmlFor="display-name"
              className="text-body-m font-semibold text-primary-dark"
            >
              表示名 *
            </label>
            <input
              id="display-name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              maxLength={100}
              className="rounded-md border border-border bg-bg-card px-3.5 py-2.5 text-body-m text-primary-dark placeholder:text-text-sage focus:border-primary focus:outline-none"
              placeholder="あなたの表示名"
              data-testid="onboarding-display-name"
            />
          </div>

          <div className="flex flex-col gap-2">
            <p className="text-body-m font-semibold text-primary-dark">
              あなたの業界・職種・スキル
            </p>
            <p className="text-body-s text-text-muted">
              関連するタグを選択すると、あなたに合ったSeedが見つかりやすくなります（任意）
            </p>
            <TagAccordionSelector
              selectedTagIds={selectedTagIds}
              onTagsChange={setSelectedTagIds}
            />
          </div>

          <div className="flex flex-col gap-2">
            <label
              htmlFor="bio"
              className="text-body-m font-semibold text-primary-dark"
            >
              自己紹介
            </label>
            <textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={3}
              className="resize-none rounded-md border border-border bg-bg-card px-3.5 py-2.5 text-body-m text-primary-dark placeholder:text-text-sage focus:border-primary focus:outline-none"
              placeholder="現場で積み上げてきた経験や専門領域を教えてください。"
              data-testid="onboarding-bio"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={!displayName.trim() || isSubmitting}
              className="rounded-lg bg-primary px-6 py-2.5 text-body-m font-medium text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
              data-testid="onboarding-submit"
            >
              {isSubmitting ? "保存中..." : "Works Logue を始める"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
