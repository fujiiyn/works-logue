"use client";

import { useState, useCallback } from "react";
import { Copy, Check } from "lucide-react";

interface LogueCopyButtonProps {
  content: string;
}

export function LogueCopyButton({ content }: LogueCopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API not available
    }
  }, [content]);

  return (
    <button
      onClick={handleCopy}
      className="flex w-full items-center justify-center gap-1.5 rounded-md border border-border bg-card px-3 py-2 text-[12px] font-medium text-primary-dark transition-colors hover:bg-bg"
      data-testid="logue-copy-button"
    >
      {copied ? (
        <>
          <Check size={14} strokeWidth={1.5} />
          コピーしました
        </>
      ) : (
        <>
          <Copy size={14} strokeWidth={1.5} />
          Logue をコピー
        </>
      )}
    </button>
  );
}
