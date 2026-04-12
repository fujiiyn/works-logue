"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/";
  const { signIn, signUp } = useAuth();

  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGoogleLogin() {
    try {
      await signIn("google");
    } catch (e) {
      setError("Googleログインに失敗しました");
    }
  }

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isSignUp) {
        await signUp(email, password);
        setError(null);
        router.push(redirect);
      } else {
        await signIn("email", { email, password });
        router.push(redirect);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "認証に失敗しました",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4"
      data-testid="login-page"
    >
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-sm">
        <h1
          className="mb-2 text-center text-heading-xl text-primary"
          data-testid="login-title"
        >
          Works Logueに{isSignUp ? "登録" : "ログイン"}
        </h1>
        <p className="mb-6 text-center text-body-s text-text-secondary">
          現場の知恵を共有し、集合知を育てましょう
        </p>

        {/* Google OAuth */}
        <button
          onClick={handleGoogleLogin}
          className="mb-4 flex w-full items-center justify-center gap-3 rounded-md border border-border py-3 text-body-m text-primary-dark transition-colors hover:bg-primary-light-bg/30"
          data-testid="login-google-button"
        >
          <span className="inline-block h-5 w-5 rounded-full bg-accent" />
          Googleでログイン
        </button>

        {/* Divider */}
        <div className="mb-4 flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-caption text-text-muted">または</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        {/* Email form */}
        <form onSubmit={handleEmailSubmit}>
          <label className="mb-1 block text-body-s text-primary-dark">
            メールアドレス
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            required
            className="mb-4 w-full rounded-md border border-border bg-white px-3 py-2.5 text-body-m text-primary-dark placeholder:text-text-sage focus:border-primary focus:outline-none"
            data-testid="login-email-input"
          />

          <label className="mb-1 block text-body-s text-primary-dark">
            パスワード
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            className="mb-4 w-full rounded-md border border-border bg-white px-3 py-2.5 text-body-m text-primary-dark placeholder:text-text-sage focus:border-primary focus:outline-none"
            data-testid="login-password-input"
          />

          {error && (
            <p className="mb-3 text-body-s text-red-600" data-testid="login-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mb-4 w-full rounded-md bg-primary py-2.5 text-body-m text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
            data-testid="login-submit-button"
          >
            {loading ? "..." : isSignUp ? "登録" : "ログイン"}
          </button>
        </form>

        {/* Toggle sign-up / sign-in */}
        <p className="text-center text-body-s">
          <button
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError(null);
            }}
            className="text-primary hover:underline"
            data-testid="login-toggle-mode"
          >
            {isSignUp
              ? "アカウントをお持ちの方はこちら"
              : "アカウントをお持ちでない方はこちら"}
          </button>
        </p>
      </div>
    </div>
  );
}
