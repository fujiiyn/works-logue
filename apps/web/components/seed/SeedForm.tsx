"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { TagAccordionSelector } from "@/components/common/TagAccordionSelector";

interface SeedType {
  id: string;
  slug: string;
  name: string;
  description: string;
}

interface CreatePlanterResponse {
  id: string;
}

const TITLE_MAX = 200;
const BODY_MAX = 10000;

export function SeedForm() {
  const router = useRouter();

  const [seedTypes, setSeedTypes] = useState<SeedType[]>([]);
  const [seedTypeId, setSeedTypeId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiFetch<SeedType[]>("/api/v1/seed-types")
      .then(setSeedTypes)
      .catch(() => {});
  }, []);

  function validate(): boolean {
    const next: Record<string, string> = {};

    if (!seedTypeId) next.seedTypeId = "Seedタイプを選択してください";
    if (!title.trim()) next.title = "タイトルを入力してください";
    else if (title.length > TITLE_MAX)
      next.title = `タイトルは${TITLE_MAX}文字以内で入力してください`;
    if (!body.trim()) next.body = "本文を入力してください";
    else if (body.length > BODY_MAX)
      next.body = `本文は${BODY_MAX}文字以内で入力してください`;

    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      const result = await apiFetch<CreatePlanterResponse>(
        "/api/v1/planters",
        {
          method: "POST",
          body: JSON.stringify({
            seed_type_id: seedTypeId,
            title: title.trim(),
            body: body.trim(),
            tag_ids: selectedTagIds,
          }),
        },
      );
      router.push(`/p/${result.id}`);
    } catch (err) {
      setErrors({
        submit:
          err instanceof Error ? err.message : "投稿に失敗しました",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} data-testid="seed-form">
      <h1
        className="mb-2 text-[22px] font-semibold text-primary-dark"
        data-testid="seed-form-title"
      >
        新しいSeedを蒔く
      </h1>
      <p className="mb-6 text-body-s text-text-secondary">
        現場のリアルな悩みや知恵を投稿して、集合知を育てましょう。完成した記事（Louge）の開花に貢献した方にはインサイトスコアが付与されます。
      </p>

      {/* Seed Type selection */}
      <div className="mb-4">
        <label className="mb-2 block text-body-m font-semibold text-primary-dark">
          投稿タイプを選んでください *
        </label>
        <div className="grid grid-cols-2 gap-2.5" data-testid="seed-type-grid">
          {seedTypes.map((st) => {
            const isSelected = seedTypeId === st.id;
            return (
              <button
                key={st.id}
                type="button"
                onClick={() => setSeedTypeId(st.id)}
                className={`rounded-lg border px-4 py-3 text-left transition-colors ${
                  isSelected
                    ? "border-primary bg-primary-light-bg"
                    : "border-border bg-bg-card hover:bg-primary-light-bg/30"
                }`}
                data-testid={`seed-type-${st.slug}`}
              >
                <span className="block text-body-m font-medium text-primary-dark">
                  {st.name}
                </span>
                <span className="block text-[11px] text-text-muted">
                  {st.description}
                </span>
              </button>
            );
          })}
        </div>
        {errors.seedTypeId && (
          <p className="mt-1 text-body-s text-red-600">{errors.seedTypeId}</p>
        )}
      </div>

      {/* Title */}
      <div className="mb-4">
        <input
          id="seed-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="例：新しい評価制度の導入でハレーションが起きた時の対処法"
          maxLength={TITLE_MAX}
          className="w-full rounded-md border border-border bg-bg-card px-3.5 py-2.5 text-body-m text-primary-dark placeholder:text-text-sage focus:border-primary focus:outline-none"
          data-testid="seed-form-title-input"
        />
        {errors.title && (
          <p className="mt-1 text-body-s text-red-600">{errors.title}</p>
        )}
      </div>

      {/* Body */}
      <div className="mb-4">
        <label
          htmlFor="seed-body"
          className="mb-2 block text-body-m font-semibold text-primary-dark"
        >
          本文 *
        </label>
        <textarea
          id="seed-body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder={`状況、問題の詳細、これまでに試したことなどを具体的に記述してください。\n社名や個人名は記載しないことをお勧めします（投稿前にAIが抽象化のサポートをします）。`}
          maxLength={BODY_MAX}
          className="h-[130px] w-full resize-none rounded-md border border-border bg-bg-card px-3.5 py-2.5 text-body-m text-primary-dark placeholder:text-text-sage focus:border-primary focus:outline-none"
          data-testid="seed-form-body-input"
        />
        {errors.body && (
          <p className="mt-1 text-body-s text-red-600">{errors.body}</p>
        )}
      </div>

      {/* Tag section */}
      <div className="mb-4">
        <label className="mb-2.5 block text-body-m font-bold text-primary-dark">
          タグ
        </label>
        <TagAccordionSelector
          selectedTagIds={selectedTagIds}
          onTagsChange={setSelectedTagIds}
        />
      </div>

      {/* Submit error */}
      {errors.submit && (
        <p
          className="mb-4 text-body-s text-red-600"
          data-testid="seed-form-error"
        >
          {errors.submit}
        </p>
      )}

      {/* Action buttons */}
      <div className="flex justify-end gap-3">
        <Link
          href="/"
          className="rounded-lg border border-border px-5 py-2.5 text-body-m text-text-secondary transition-colors hover:bg-primary-light-bg/30"
          data-testid="seed-form-cancel"
        >
          キャンセル
        </Link>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-primary px-6 py-2.5 text-body-m font-medium text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
          data-testid="seed-form-submit"
        >
          {submitting ? "投稿中..." : "Seedを蒔く"}
        </button>
      </div>
    </form>
  );
}
