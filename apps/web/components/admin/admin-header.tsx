"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";

interface AdminHeaderProps {
  user: {
    id: string;
    display_name: string;
  };
}

export function AdminHeader({ user }: AdminHeaderProps) {
  const router = useRouter();
  const { signOut } = useAuth();

  async function handleLogout() {
    await signOut();
    router.push("/login");
  }

  return (
    <header
      data-testid="admin-header"
      className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-bg-card px-6"
    >
      <Link href="/admin" className="flex items-center gap-2">
        <Image
          src="/img/works-logue-logo-icon.svg"
          alt="Works Logue"
          width={28}
          height={28}
          className="h-7 w-7 object-contain"
        />
        <span className="text-heading-l font-semibold text-primary-dark">
          Works Logue
        </span>
        <span className="ml-1 rounded bg-primary-dark px-1.5 py-0.5 text-[11px] font-semibold text-white">
          Admin
        </span>
      </Link>

      <div className="flex items-center gap-4">
        <Link
          href="/"
          data-testid="admin-header-back-to-site"
          className="text-body-s text-text-secondary hover:text-primary-dark"
        >
          公開サイトに戻る
        </Link>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-light-bg text-body-m font-semibold text-primary">
            {user.display_name.charAt(0).toUpperCase()}
          </div>
          <span className="text-body-s text-primary-dark">
            {user.display_name}
          </span>
        </div>
        <button
          type="button"
          data-testid="admin-header-logout"
          onClick={handleLogout}
          className="flex items-center gap-1 rounded border border-border bg-white px-2.5 py-1.5 text-body-s text-text-secondary hover:bg-bg-card"
        >
          <LogOut className="h-4 w-4" />
          ログアウト
        </button>
      </div>
    </header>
  );
}
