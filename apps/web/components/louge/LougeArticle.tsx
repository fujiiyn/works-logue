"use client";

import ReactMarkdown from "react-markdown";
import { formatRelativeTime } from "@/lib/format-time";

interface LougeArticleProps {
  content: string;
  generatedAt: string;
}

export function LougeArticle({ content, generatedAt }: LougeArticleProps) {
  return (
    <div data-testid="louge-article">
      {/* Article label */}
      <div className="mb-3 flex items-center gap-2">
        <h2 className="text-heading-m text-primary-dark">
          Louge（開花記事）
        </h2>
        <span className="text-caption text-text-muted">
          {formatRelativeTime(generatedAt)}に開花
        </span>
      </div>

      {/* Markdown content */}
      <div className="prose-louge mb-6 max-w-none" data-testid="louge-article-content">
        <ReactMarkdown
          components={{
            h1: ({ children }) => (
              <div className="mb-4 rounded-md bg-primary-light-bg px-3 py-2">
                <span className="text-[13px] font-medium text-primary">
                  パターン名：{children}
                </span>
              </div>
            ),
            h2: ({ children }) => (
              <h3 className="mb-2 mt-5 text-[14px] font-bold text-primary">
                {children}
              </h3>
            ),
            p: ({ children }) => (
              <p className="mb-3 text-[13px] leading-[1.8] text-primary-dark">
                {children}
              </p>
            ),
            hr: () => <div className="my-5 h-px bg-border" />,
            ul: ({ children }) => (
              <ul className="mb-3 ml-4 list-disc space-y-1 text-[13px] leading-[1.8] text-primary-dark">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="mb-3 ml-4 list-decimal space-y-1 text-[13px] leading-[1.8] text-primary-dark">
                {children}
              </ol>
            ),
            blockquote: ({ children }) => (
              <blockquote className="my-3 border-l-2 border-primary pl-3 text-[13px] leading-[1.8] text-text-secondary">
                {children}
              </blockquote>
            ),
            strong: ({ children }) => (
              <strong className="font-bold text-primary-dark">{children}</strong>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
