"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { MessageSquare, Users } from "lucide-react";
import { formatRelativeTime } from "@/lib/format-time";
import { apiFetch } from "@/lib/api-client";
import { useRightSidebar } from "@/contexts/right-sidebar-context";
import { LogThread } from "@/components/log/LogThread";
import { LogComposer } from "@/components/log/LogComposer";
import { ScoreCard } from "@/components/planter/ScoreCard";

interface StructureParts {
  context: boolean;
  problem: boolean;
  solution: boolean;
  name: boolean;
}

interface PlanterDetail {
  id: string;
  title: string;
  body: string;
  status: string;
  seed_type: { slug: string; name: string };
  user: { id: string; display_name: string; avatar_url: string | null };
  tags: { id: string; name: string; category: string }[];
  log_count: number;
  contributor_count: number;
  progress: number;
  structure_fulfillment: number;
  maturity_score: number | null;
  structure_parts: StructureParts | null;
  bloom_threshold: number;
  created_at: string;
}

interface ScoreResponse {
  score: {
    id: string;
    status: string;
    log_count: number;
    contributor_count: number;
    progress: number;
    structure_fulfillment: number;
    maturity_score: number | null;
    structure_parts: StructureParts | null;
  };
  score_pending: boolean;
  last_scored_at: string | null;
}

const STATUS_LABELS: Record<string, string> = {
  seed: "Seed",
  sprout: "Sprout",
  louge: "Louge",
};

const POLL_INTERVALS = [3000, 5000, 10000];

export function PlanterDetailClient({
  planter: initialPlanter,
  bloomThreshold,
}: {
  planter: PlanterDetail;
  bloomThreshold: number;
}) {
  const [planter, setPlanter] = useState(initialPlanter);
  const [scorePending, setScorePending] = useState(false);
  const [replyTo, setReplyTo] = useState<{
    id: string;
    displayName: string;
  } | null>(null);
  const logThreadKeyRef = useRef(0);
  const { setContent } = useRightSidebar();
  const isLouge = planter.status === "louge";

  // Score polling
  const pollScore = useCallback(
    async (attempt: number = 0) => {
      if (attempt >= POLL_INTERVALS.length) {
        setScorePending(false);
        return;
      }

      await new Promise((r) => setTimeout(r, POLL_INTERVALS[attempt]));

      try {
        const data = await apiFetch<ScoreResponse>(
          `/api/v1/planters/${planter.id}/score`,
        );
        const s = data.score;
        setPlanter((prev) => ({
          ...prev,
          status: s.status,
          log_count: s.log_count,
          contributor_count: s.contributor_count,
          progress: s.progress,
          structure_fulfillment: s.structure_fulfillment,
          maturity_score: s.maturity_score,
          structure_parts: s.structure_parts,
        }));

        if (data.score_pending) {
          pollScore(attempt + 1);
        } else {
          setScorePending(false);
        }
      } catch {
        setScorePending(false);
      }
    },
    [planter.id],
  );

  // Update right sidebar with ScoreCard
  useEffect(() => {
    setContent(
      <ScoreCard
        status={planter.status}
        structureFulfillment={planter.structure_fulfillment}
        maturityScore={planter.maturity_score}
        logCount={planter.log_count}
        contributorCount={planter.contributor_count}
        progress={planter.progress}
        bloomThreshold={bloomThreshold}
        structureParts={planter.structure_parts}
        scorePending={scorePending}
      />,
    );
    return () => setContent(null);
  }, [
    planter.status,
    planter.structure_fulfillment,
    planter.maturity_score,
    planter.log_count,
    planter.contributor_count,
    planter.progress,
    planter.structure_parts,
    bloomThreshold,
    scorePending,
    setContent,
  ]);

  const handleLogCreated = useCallback(
    (response: {
      log: { id: string; planter_id: string };
      planter: {
        status: string;
        log_count: number;
        contributor_count: number;
        progress: number;
        structure_fulfillment: number;
        maturity_score: number | null;
        structure_parts: StructureParts | null;
      };
      score_pending: boolean;
    }) => {
      // Update planter with immediate response data
      setPlanter((prev) => ({
        ...prev,
        status: response.planter.status,
        log_count: response.planter.log_count,
        contributor_count: response.planter.contributor_count,
        progress: response.planter.progress,
        structure_fulfillment: response.planter.structure_fulfillment,
        maturity_score: response.planter.maturity_score,
        structure_parts: response.planter.structure_parts,
      }));

      // Force LogThread to refetch
      logThreadKeyRef.current += 1;

      // Start score polling if pending
      if (response.score_pending) {
        setScorePending(true);
        pollScore(0);
      }
    },
    [pollScore],
  );

  const handleReply = useCallback(
    (logId: string) => {
      // We don't have the display name here, but we can set a generic one
      setReplyTo({ id: logId, displayName: "Log" });
    },
    [],
  );

  return (
    <div
      className="-mb-6 flex min-h-[calc(100vh-3.5rem)] flex-col"
      data-testid="planter-detail"
    >
      <div className="flex-1">
        {/* Meta row */}
        <div className="mb-3 flex items-center gap-1.5 text-caption text-text-muted">
          <span
            className={`inline-block rounded-sm px-[6px] py-[1px] text-caption font-medium ${
              isLouge
                ? "bg-primary text-white"
                : "bg-primary-light-bg text-primary"
            }`}
          >
            {STATUS_LABELS[planter.status] ?? planter.status}
          </span>
          <span>{planter.seed_type.name}</span>
          <span>·</span>
          {planter.user.avatar_url ? (
            <img
              src={planter.user.avatar_url}
              alt=""
              className="h-4 w-4 rounded-full object-cover"
            />
          ) : (
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary-light-bg text-[9px] text-primary">
              {planter.user.display_name.charAt(0)}
            </span>
          )}
          <span>{planter.user.display_name}</span>
          <span>·</span>
          <span>{formatRelativeTime(planter.created_at)}</span>
        </div>

        {/* Title */}
        <h1
          className="mb-4 text-[18px] font-semibold leading-[1.55] text-primary-dark"
          data-testid="planter-detail-title"
        >
          {planter.title}
        </h1>

        {/* Body */}
        <div className="mb-5 max-w-[700px]">
          <p className="whitespace-pre-wrap text-[14px] leading-[1.7] text-text-secondary">
            {planter.body}
          </p>
        </div>

        {/* Tags */}
        {planter.tags.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-1.5">
            {planter.tags.map((tag) => (
              <span
                key={tag.id}
                className="rounded-sm border border-border px-[8px] py-[3px] text-caption text-text-secondary"
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}

        {/* Stats */}
        <div className="mb-5 flex gap-3 text-body-s text-text-muted">
          <span className="flex items-center gap-1">
            <MessageSquare size={14} strokeWidth={1.5} />
            {planter.log_count} logs
          </span>
          <span className="flex items-center gap-1">
            <Users size={14} strokeWidth={1.5} />
            {planter.contributor_count} contributors
          </span>
        </div>

        {/* Divider */}
        <div className="mb-5 h-px bg-border" />

        {/* Logs section */}
        <h2 className="mb-4 text-heading-m text-primary-dark">Logs</h2>

        <LogThread
          key={logThreadKeyRef.current}
          planterId={planter.id}
          onReply={handleReply}
        />
      </div>

      {/* Bottom sticky input bar */}
      <LogComposer
        planterId={planter.id}
        planterStatus={planter.status}
        replyTo={replyTo}
        onCancelReply={() => setReplyTo(null)}
        onLogCreated={handleLogCreated}
      />
    </div>
  );
}
