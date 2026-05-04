"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  perPage: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, perPage, total, onPageChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const canPrev = page > 1;
  const canNext = page < totalPages;

  return (
    <div className="flex items-center justify-between gap-3 py-3 text-sm text-primary-dark/70">
      <button
        type="button"
        data-testid="pagination-prev"
        disabled={!canPrev}
        onClick={() => canPrev && onPageChange(page - 1)}
        className="flex items-center gap-1 rounded border border-border bg-white px-3 py-1.5 disabled:opacity-40"
      >
        <ChevronLeft className="h-4 w-4" />
        前へ
      </button>
      <span data-testid="pagination-info">
        {page} / {totalPages} ページ ・ 全 {total} 件
      </span>
      <button
        type="button"
        data-testid="pagination-next"
        disabled={!canNext}
        onClick={() => canNext && onPageChange(page + 1)}
        className="flex items-center gap-1 rounded border border-border bg-white px-3 py-1.5 disabled:opacity-40"
      >
        次へ
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
