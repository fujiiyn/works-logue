"use client";

import Link from "next/link";
import Image from "next/image";
import { Menu, Plus } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/contexts/auth-context";

export function Header() {
  const { user, isLoading, signOut } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      <header
        className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-bg-card px-4 md:px-6"
        data-testid="header"
      >
        {/* Left: mobile hamburger + logo */}
        <div className="flex items-center gap-3">
          <button
            className="md:hidden"
            onClick={() => {
              const event = new CustomEvent("toggle-sidebar");
              window.dispatchEvent(event);
            }}
            data-testid="header-hamburger"
            aria-label="メニューを開く"
          >
            <Menu size={20} strokeWidth={1.5} />
          </button>

          <Link href="/" className="flex items-center gap-2" data-testid="header-logo">
            <Image
              src="/img/works-logue-logo-icon.svg"
              alt="Works Logue"
              width={32}
              height={28}              
              className="h-7 w-auto object-contain"
            />
            <span className="hidden text-heading-l font-bold text-primary-dark md:block">
              Works Logue
            </span>
          </Link>
        </div>

        {/* Right: actions */}
        <div className="flex items-center gap-3">
          {!isLoading && !user && (
            <Link
              href="/login"
              className="text-body-m text-text-secondary hover:text-primary-dark"
              data-testid="header-login-button"
            >
              ログイン
            </Link>
          )}

          {!isLoading && user && (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-1"
                data-testid="header-user-menu"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-light-bg text-body-s text-primary">
                  {user.display_name.charAt(0)}
                </div>
              </button>

              {dropdownOpen && (
                <div className="absolute right-0 top-10 z-50 w-48 rounded-lg border border-border bg-bg-card py-1 shadow-md">
                  <Link
                    href={`/user/${user.id}`}
                    className="block px-4 py-2 text-body-m text-primary-dark hover:bg-primary-light-bg"
                    onClick={() => setDropdownOpen(false)}
                    data-testid="header-profile-link"
                  >
                    プロフィール
                  </Link>
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      signOut();
                    }}
                    className="block w-full px-4 py-2 text-left text-body-m text-primary-dark hover:bg-primary-light-bg"
                    data-testid="header-logout-button"
                  >
                    ログアウト
                  </button>
                </div>
              )}
            </div>
          )}

          <Link
            href={user ? "/seed/new" : "/login?redirect=/seed/new"}
            className="flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-body-m text-white transition-colors hover:bg-primary-dark"
            data-testid="header-seed-button"
          >
            <Plus size={16} strokeWidth={1.5} />
            <span>Seed</span>
          </Link>
        </div>
      </header>

      {/* Dropdown backdrop */}
      {dropdownOpen && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => setDropdownOpen(false)}
        />
      )}
    </>
  );
}
