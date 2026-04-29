"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Camera } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { useRightSidebar } from "@/contexts/right-sidebar-context";
import { apiFetch, apiFetchUpload } from "@/lib/api-client";
import { InitialAvatar } from "@/components/user/InitialAvatar";
import { TagAccordionSelector } from "@/components/common/TagAccordionSelector";

interface TagItem {
  id: string;
  name: string;
  category: string;
}

export default function ProfileEditPage() {
  const { user, isLoading: authLoading, refreshUser } = useAuth();
  const router = useRouter();
  const { setContent } = useRightSidebar();

  const [displayName, setDisplayName] = useState("");
  const [headline, setHeadline] = useState("");
  const [bio, setBio] = useState("");
  const [location, setLocation] = useState("");
  const [xUrl, setXUrl] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [wantedlyUrl, setWantedlyUrl] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [tagIds, setTagIds] = useState<string[]>([]);
  const [tagNames, setTagNames] = useState<string[]>([]);

  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [coverPreview, setCoverPreview] = useState<string | null>(null);
  const [avatarUploaded, setAvatarUploaded] = useState(false);
  const [coverUploaded, setCoverUploaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const avatarInputRef = useRef<HTMLInputElement>(null);
  const coverInputRef = useRef<HTMLInputElement>(null);

  // Load current profile
  useEffect(() => {
    if (!user) return;
    apiFetch<{
      display_name: string;
      headline: string | null;
      bio: string | null;
      avatar_url: string | null;
      cover_url: string | null;
      location: string | null;
      x_url: string | null;
      linkedin_url: string | null;
      wantedly_url: string | null;
      website_url: string | null;
    }>("/api/v1/users/me").then((data) => {
      setDisplayName(data.display_name);
      setHeadline(data.headline ?? "");
      setBio(data.bio ?? "");
      setLocation(data.location ?? "");
      setXUrl(data.x_url ?? "");
      setLinkedinUrl(data.linkedin_url ?? "");
      setWantedlyUrl(data.wantedly_url ?? "");
      setWebsiteUrl(data.website_url ?? "");
      setAvatarPreview(data.avatar_url);
      setCoverPreview(data.cover_url);
    });

    apiFetch<{
      user: unknown;
      tags: TagItem[];
    }>(`/api/v1/users/${user.id}`).then((data) => {
      setTagIds(data.tags.map((t) => t.id));
      setTagNames(data.tags.map((t) => t.name));
    });
  }, [user]);

  // beforeunload warning (D2)
  useEffect(() => {
    function handleBeforeUnload(e: BeforeUnloadEvent) {
      if (dirty || avatarUploaded || coverUploaded) {
        e.preventDefault();
      }
    }
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [dirty, avatarUploaded, coverUploaded]);

  // Redirect if not logged in
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, user, router]);

  // Right sidebar: preview + save/cancel (Figma: 371:159)
  useEffect(() => {
    if (!user) return;

    setContent(
      <EditSidebar
        avatarPreview={avatarPreview}
        displayName={displayName}
        headline={headline}
        tagNames={tagNames}
        userId={user.id}
        saving={saving}
        canSave={!!displayName.trim()}
        onSave={() => {
          // Trigger save via custom event since sidebar can't call handleSave directly
          window.dispatchEvent(new CustomEvent("profile-edit-save"));
        }}
        onCancel={() => router.push(`/user/${user.id}`)}
      />,
    );

    return () => setContent(null);
  }, [user, avatarPreview, displayName, headline, tagNames, saving, setContent, router]);

  // Listen for save event from sidebar
  useEffect(() => {
    function onSaveEvent() {
      handleSave();
    }
    window.addEventListener("profile-edit-save", onSaveEvent);
    return () => window.removeEventListener("profile-edit-save", onSaveEvent);
  });

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      setError("アバター画像は2MB以下にしてください");
      return;
    }
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setError("JPEGまたはPNG画像のみ対応しています");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => setAvatarPreview(reader.result as string);
    reader.readAsDataURL(file);

    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await apiFetchUpload<{ url: string }>(
        "/api/v1/users/me/avatar",
        formData,
      );
      setAvatarPreview(res.url);
      setAvatarUploaded(true);
      setError(null);
    } catch (err: any) {
      setError(err.message || "アバターのアップロードに失敗しました");
    }
  }

  async function handleCoverChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setError("カバー画像は5MB以下にしてください");
      return;
    }
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setError("JPEGまたはPNG画像のみ対応しています");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => setCoverPreview(reader.result as string);
    reader.readAsDataURL(file);

    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await apiFetchUpload<{ url: string }>(
        "/api/v1/users/me/cover",
        formData,
      );
      setCoverPreview(res.url);
      setCoverUploaded(true);
      setError(null);
    } catch (err: any) {
      setError(err.message || "カバー画像のアップロードに失敗しました");
    }
  }

  async function handleSave() {
    if (!user) return;
    setSaving(true);
    setError(null);
    try {
      await apiFetch("/api/v1/users/me", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: displayName,
          headline: headline || null,
          bio: bio || null,
          location: location || null,
          x_url: xUrl || null,
          linkedin_url: linkedinUrl || null,
          wantedly_url: wantedlyUrl || null,
          website_url: websiteUrl || null,
          tag_ids: tagIds,
        }),
      });
      setDirty(false);
      setAvatarUploaded(false);
      setCoverUploaded(false);
      await refreshUser();
      router.push(`/user/${user.id}`);
    } catch (err: any) {
      setError(err.message || "保存に失敗しました");
    } finally {
      setSaving(false);
    }
  }

  if (authLoading || !user) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[720px]" data-testid="profile-edit-page">
      {/* Header */}
      <button
        onClick={() => router.push(`/user/${user.id}`)}
        className="mb-4 flex items-center gap-1 text-body-m text-text-secondary hover:text-primary"
        data-testid="profile-edit-back"
      >
        <ArrowLeft size={16} strokeWidth={1.5} />
        プロフィールに戻る
      </button>

      <h1 className="mb-2 text-heading-xl text-primary-dark">
        プロフィールを編集
      </h1>
      <p className="mb-6 text-[14px] text-text-secondary">
        あなたの専門性や経験を伝えるプロフィールを作りましょう。変更はすぐに反映されます。
      </p>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-body-s text-red-600">
          {error}
        </div>
      )}

      {/* Visual section */}
      <h2 className="mb-2 text-heading-m text-primary-dark">
        ビジュアル
        <span className="ml-2 text-caption font-normal text-text-muted">任意</span>
      </h2>

      {/* Cover Image */}
      <div className="mb-4">
        <div
          className="relative h-[140px] cursor-pointer overflow-hidden rounded-lg"
          onClick={() => coverInputRef.current?.click()}
        >
          {coverPreview ? (
            <img
              src={coverPreview}
              alt=""
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="h-full w-full bg-gradient-to-r from-[#214740] via-[#2e6157] to-[#387063]" />
          )}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="rounded-md bg-black/50 px-4 py-1.5 text-body-s font-medium text-white">
              カバー画像を変更
            </span>
          </div>
        </div>
        <input
          ref={coverInputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={handleCoverChange}
          data-testid="profile-edit-cover-input"
        />
      </div>

      {/* Avatar */}
      <div className="mb-6 flex items-center gap-4">
        <div
          className="relative shrink-0 cursor-pointer"
          onClick={() => avatarInputRef.current?.click()}
        >
          {avatarPreview ? (
            <img
              src={avatarPreview}
              alt=""
              className="h-[76px] w-[76px] rounded-full object-cover"
            />
          ) : (
            <InitialAvatar
              displayName={displayName || "U"}
              userId={user.id}
              size={76}
            />
          )}
          <div className="absolute bottom-0 right-0 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white shadow">
            <Camera size={12} />
          </div>
        </div>
        <div>
          <button
            onClick={() => avatarInputRef.current?.click()}
            className="rounded-md border border-border bg-white px-3 py-1.5 text-body-s font-medium text-primary hover:bg-primary-light-bg"
          >
            アバターを変更
          </button>
          <p className="mt-1 text-caption text-text-muted">
            JPG, PNG, 2MB以下
          </p>
        </div>
        <input
          ref={avatarInputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={handleAvatarChange}
          data-testid="profile-edit-avatar-input"
        />
      </div>

      <div className="mb-6 border-t border-border" />

      {/* Text Fields */}
      <div className="space-y-5">
        <Field
          label="ヘッドライン"
          hint="あなたの専門性を一行で表現してください"
          value={headline}
          onChange={(v) => { setHeadline(v); setDirty(true); }}
          maxLength={60}
          placeholder="例: 人事制度設計のスペシャリスト"
          optional
        />

        <div className="border-t border-border" />

        <Field
          label="表示名"
          value={displayName}
          onChange={(v) => { setDisplayName(v); setDirty(true); }}
          maxLength={100}
          required
        />

        <div>
          <label className="mb-1 flex items-center gap-2 text-heading-m text-primary-dark">
            自己紹介
            <span className="text-caption font-normal text-text-muted">任意</span>
            <span className="ml-auto text-caption font-normal text-text-muted">
              {bio.length}/200
            </span>
          </label>
          <textarea
            value={bio}
            onChange={(e) => { setBio(e.target.value); setDirty(true); }}
            maxLength={200}
            rows={3}
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-body-m text-primary-dark outline-none focus:border-primary"
            data-testid="profile-edit-bio"
          />
        </div>

        <div className="border-t border-border" />

        {/* Tags */}
        <div>
          <h2 className="mb-1 text-heading-m text-primary-dark">タグ設定</h2>
          <p className="mb-3 text-body-s text-text-muted">
            プロフィールに表示するタグを選択してください。
          </p>
          <TagAccordionSelector
            selectedTagIds={tagIds}
            onTagsChange={(ids: string[]) => { setTagIds(ids); setDirty(true); }}
          />
        </div>

        <div className="border-t border-border" />

        <Field
          label="居住地"
          value={location}
          onChange={(v) => { setLocation(v); setDirty(true); }}
          maxLength={100}
          placeholder="例: 東京都"
          optional
        />

        <div className="border-t border-border" />

        <div>
          <h2 className="mb-1 flex items-center gap-2 text-heading-m text-primary-dark">
            SNSリンク
            <span className="text-caption font-normal text-text-muted">任意</span>
          </h2>
          <p className="mb-3 text-body-s text-text-muted">
            他のプラットフォームのプロフィールURLを追加できます。
          </p>
          <div className="space-y-3">
            <SmallField label="X (Twitter)" value={xUrl} onChange={(v) => { setXUrl(v); setDirty(true); }} placeholder="https://x.com/username" />
            <SmallField label="LinkedIn" value={linkedinUrl} onChange={(v) => { setLinkedinUrl(v); setDirty(true); }} placeholder="https://linkedin.com/in/username" />
            <SmallField label="Wantedly" value={wantedlyUrl} onChange={(v) => { setWantedlyUrl(v); setDirty(true); }} placeholder="https://wantedly.com/id/username" />
            <SmallField label="個人サイト" value={websiteUrl} onChange={(v) => { setWebsiteUrl(v); setDirty(true); }} placeholder="https://example.com" />
          </div>
        </div>

        <div className="border-t border-border" />
      </div>

      {/* Mobile-only actions (desktop uses sidebar) */}
      <div className="mt-8 flex gap-3 xl:hidden">
        <button
          onClick={handleSave}
          disabled={saving || !displayName.trim()}
          className="flex-1 rounded-lg bg-primary py-3 text-[14px] font-bold text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
          data-testid="profile-edit-save"
        >
          {saving ? "保存中..." : "保存する"}
        </button>
        <button
          onClick={() => router.push(`/user/${user.id}`)}
          className="flex-1 rounded-lg border border-border py-3 text-[14px] font-medium text-primary-dark transition-colors hover:bg-primary-light-bg"
          data-testid="profile-edit-cancel"
        >
          キャンセル
        </button>
      </div>
    </div>
  );
}

// --- Right sidebar preview (Figma: 371:159-172) ---

function EditSidebar({
  avatarPreview,
  displayName,
  headline,
  tagNames,
  userId,
  saving,
  canSave,
  onSave,
  onCancel,
}: {
  avatarPreview: string | null;
  displayName: string;
  headline: string;
  tagNames: string[];
  userId: string;
  saving: boolean;
  canSave: boolean;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="space-y-4">
      {/* Preview label */}
      <h3 className="text-heading-m text-text-secondary">プレビュー</h3>

      {/* Preview card */}
      <div className="rounded-lg border border-border bg-bg-card p-4">
        <div className="flex items-start gap-3">
          {avatarPreview ? (
            <img
              src={avatarPreview}
              alt=""
              className="h-11 w-11 shrink-0 rounded-full object-cover"
            />
          ) : (
            <InitialAvatar
              displayName={displayName || "U"}
              userId={userId}
              size={44}
            />
          )}
          <div className="min-w-0">
            <p className="truncate text-[14px] font-bold text-primary-dark">
              {displayName || "表示名"}
            </p>
            {headline && (
              <p className="truncate text-[10px] text-primary">{headline}</p>
            )}
          </div>
        </div>
        {tagNames.length > 0 && (
          <div className="mt-2.5 flex flex-wrap gap-1">
            {tagNames.slice(0, 3).map((name) => (
              <span
                key={name}
                className="rounded-full bg-primary-light-bg px-2 py-0.5 text-[8px] text-primary"
              >
                {name}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Save button */}
      <button
        onClick={onSave}
        disabled={saving || !canSave}
        className="w-full rounded-lg bg-primary py-3 text-[14px] font-bold text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
        data-testid="profile-edit-save-sidebar"
      >
        {saving ? "保存中..." : "保存する"}
      </button>

      {/* Cancel button */}
      <button
        onClick={onCancel}
        className="w-full rounded-lg border border-border bg-white py-3 text-[14px] font-medium text-primary-dark transition-colors hover:bg-primary-light-bg"
        data-testid="profile-edit-cancel-sidebar"
      >
        キャンセル
      </button>
    </div>
  );
}

// --- Field components ---

function Field({
  label,
  hint,
  value,
  onChange,
  maxLength,
  required,
  optional,
  placeholder,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  maxLength?: number;
  required?: boolean;
  optional?: boolean;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-1 flex items-center gap-2 text-heading-m text-primary-dark">
        {label}
        {required && <span className="text-caption font-normal text-primary">必須</span>}
        {optional && <span className="text-caption font-normal text-text-muted">任意</span>}
        {maxLength && (
          <span className="ml-auto text-caption font-normal text-text-muted">
            {value.length}/{maxLength}
          </span>
        )}
      </label>
      {hint && (
        <p className="mb-1 text-body-s text-text-muted">{hint}</p>
      )}
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={maxLength}
        placeholder={placeholder}
        className="w-full rounded-lg border border-border bg-white px-3 py-2 text-body-m text-primary-dark outline-none focus:border-primary"
      />
    </div>
  );
}

function SmallField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-1 block text-body-s font-medium text-primary-dark">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-border bg-white px-3 py-2 text-body-s text-primary-dark outline-none focus:border-primary"
      />
    </div>
  );
}
