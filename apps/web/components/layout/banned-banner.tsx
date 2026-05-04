"use client";

import { AlertTriangle } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";

export function BannedBanner() {
  const { user } = useAuth();
  if (!user?.is_banned) return null;

  return (
    <div
      role="alert"
      data-testid="banned-banner"
      className="flex items-start gap-3 border-b border-red-300 bg-red-50 px-6 py-3 text-red-900"
    >
      <AlertTriangle aria-hidden className="mt-0.5 h-5 w-5 shrink-0" />
      <p className="text-sm leading-relaxed">
        あなたのアカウントは現在制限されています。投稿・編集・フォロー操作はできません。
        詳細は運営までお問い合わせください。
      </p>
    </div>
  );
}
