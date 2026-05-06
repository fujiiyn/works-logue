"use client";

import Link from "next/link";
import { useEffect, useState, useCallback, useRef } from "react";
import { MessageSquare, Users, ChevronDown, ChevronRight, Flower2 } from "lucide-react";
import { formatRelativeTime } from "@/lib/format-time";
import { apiFetch } from "@/lib/api-client";
import { supabase } from "@/lib/supabase";
import { useRightSidebar } from "@/contexts/right-sidebar-context";
import {
  LogThread,
  type LogThreadHandle,
  type RealtimeLogRow,
} from "@/components/log/LogThread";
import { LogComposer } from "@/components/log/LogComposer";
import { ScoreCard } from "@/components/planter/ScoreCard";
import { PlanterFollowButton } from "@/components/planter/PlanterFollowButton";
import { LougeArticle } from "@/components/louge/LougeArticle";
import { ContributorsSidebar } from "@/components/louge/ContributorsSidebar";

interface RealtimePlanterRow {
  id: string;
  status: string;
  log_count: number;
  contributor_count: number;
  progress: number;
  structure_fulfillment: number;
  maturity_score: number | null;
  louge_content: string | null;
  louge_generated_at: string | null;
}

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
  louge_content: string | null;
  louge_generated_at: string | null;
  bloom_pending: boolean;
  is_following: boolean;
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

interface Contributor {
  user_id: string;
  display_name: string;
  avatar_url: string | null;
  insight_score_earned: number;
  log_count: number;
  is_seed_author: boolean;
}

const STATUS_LABELS: Record<string, string> = {
  seed: "Seed",
  sprout: "Sprout",
  louge: "Louge",
};

const POLL_INTERVALS = [3000, 5000, 10000];
const BLOOM_POLL_INTERVALS = [3000, 5000, 10000, 10000, 10000, 10000];
const BLOOM_TIMEOUT_MS = 60000;

export function PlanterDetailClient({
  planter: initialPlanter,
}: {
  planter: PlanterDetail;
}) {
  const [planter, setPlanter] = useState(initialPlanter);
  const [scorePending, setScorePending] = useState(false);
  const [bloomPending, setBloomPending] = useState(initialPlanter.bloom_pending);
  const [bloomTimedOut, setBloomTimedOut] = useState(false);
  const [seedExpanded, setSeedExpanded] = useState(false);
  const [contributors, setContributors] = useState<Contributor[]>([]);
  const [contributorsLoading, setContributorsLoading] = useState(false);
  const [replyTo, setReplyTo] = useState<{
    id: string;
    displayName: string;
  } | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const logThreadRef = useRef<LogThreadHandle>(null);
  // Tracked imperatively so handleRealtimeLogInsert can react synchronously
  // without waiting for a re-render.
  const isAtBottomRef = useRef(true);
  // IDs of logs the current user just posted via the composer. Realtime
  // echoes these back, but they should not bump unreadCount — the user is
  // already at the bottom (we scrolled them there) and the message is theirs.
  const ownPostIdsRef = useRef<Set<string>>(new Set());
  // Re-entry guard for pollBloom. Without it, a second trigger (e.g. another
  // pollScore landing on "louge", or the mount-time effect overlapping with a
  // user-posted log's pollScore) starts a parallel chain with its own
  // BLOOM_TIMEOUT_MS — multiplying the request rate against /api/v1/planters.
  const bloomPollingRef = useRef(false);
  const { setContent } = useRightSidebar();
  const isLouge = planter.status === "louge";

  // Record view (fire-and-forget)
  useEffect(() => {
    apiFetch(`/api/v1/planters/${initialPlanter.id}/view`, { method: "POST" }).catch(
      () => {},
    );
  }, [initialPlanter.id]);

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

        // Check if bloomed
        if (s.status === "louge") {
          setScorePending(false);
          setBloomPending(true);
          pollBloom(0);
          return;
        }

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

  // Bloom polling (check for louge_content)
  const pollBloom = useCallback(
    async (attempt: number = 0) => {
      if (bloomPollingRef.current) return;
      bloomPollingRef.current = true;
      const startTime = Date.now();

      const poll = async (idx: number) => {
        if (Date.now() - startTime > BLOOM_TIMEOUT_MS) {
          setBloomTimedOut(true);
          setBloomPending(false);
          bloomPollingRef.current = false;
          return;
        }

        const interval = BLOOM_POLL_INTERVALS[Math.min(idx, BLOOM_POLL_INTERVALS.length - 1)];
        await new Promise((r) => setTimeout(r, interval));

        try {
          const data = await apiFetch<PlanterDetail>(
            `/api/v1/planters/${planter.id}`,
          );

          if (data.louge_content) {
            setPlanter((prev) => ({
              ...prev,
              louge_content: data.louge_content,
              louge_generated_at: data.louge_generated_at,
              bloom_pending: false,
            }));
            setBloomPending(false);
            bloomPollingRef.current = false;
            // Fetch contributors
            fetchContributors();
          } else {
            poll(idx + 1);
          }
        } catch {
          // Transient fetch error mid-bloom (Cloud Run cold start, network
          // blip, Vertex AI latency). Clearing bloomPending here would drop
          // the user back to the Sprout UI while bloom is still in flight.
          // Retry until the outer BLOOM_TIMEOUT_MS guard.
          poll(idx + 1);
        }
      };

      poll(attempt);
    },
    [planter.id],
  );

  // Fetch contributors for louge state
  const fetchContributors = useCallback(async () => {
    setContributorsLoading(true);
    try {
      const data = await apiFetch<{ contributors: Contributor[] }>(
        `/api/v1/planters/${planter.id}/contributors`,
      );
      setContributors(data.contributors);
    } catch {
      // Silently fail
    } finally {
      setContributorsLoading(false);
    }
  }, [planter.id]);

  // Initial bloom polling if page loaded in bloom_pending state
  useEffect(() => {
    if (bloomPending && !bloomTimedOut) {
      pollBloom(0);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Supabase Realtime: subscribe to planters UPDATE to reflect score changes,
  // status transitions and Louge bloom across browsers without polling. The
  // user's own posts still drive pollScore for snappier local feedback; for
  // OTHER users' / AI posts this is the only sync path.
  useEffect(() => {
    const planterId = initialPlanter.id;
    const channel = supabase
      .channel(`planter:${planterId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "planters",
          filter: `id=eq.${planterId}`,
        },
        async (payload) => {
          const row = payload.new as RealtimePlanterRow;
          // Defensive: ignore malformed payloads (e.g. future schema drift).
          if (typeof row?.status !== "string") return;

          // structure_parts is not a column on planters; pull it from /score
          // (which reads the latest LougeScoreSnapshot).
          let structureParts: StructureParts | null = null;
          try {
            const data = await apiFetch<ScoreResponse>(
              `/api/v1/planters/${planterId}/score`,
            );
            structureParts = data.score.structure_parts;
          } catch {
            // leave structure_parts unchanged on fetch failure
          }

          setPlanter((prev) => ({
            ...prev,
            status: row.status,
            log_count: row.log_count,
            contributor_count: row.contributor_count,
            progress: row.progress,
            structure_fulfillment: row.structure_fulfillment,
            maturity_score: row.maturity_score,
            structure_parts: structureParts ?? prev.structure_parts,
            louge_content: row.louge_content ?? prev.louge_content,
            louge_generated_at:
              row.louge_generated_at ?? prev.louge_generated_at,
          }));

          // Score has landed — clear the calculating indicator.
          setScorePending(false);

          // Bloom transition handling
          if (row.status === "louge" && !row.louge_content) {
            setBloomPending(true);
          } else if (row.louge_content) {
            setBloomPending(false);
            void fetchContributors();
          }
        },
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [initialPlanter.id, fetchContributors]);

  // Fetch contributors on initial load if already bloomed
  useEffect(() => {
    if (isLouge && planter.louge_content) {
      fetchContributors();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Update right sidebar
  useEffect(() => {
    if (isLouge && planter.louge_content) {
      setContent(
        <ContributorsSidebar
          contributors={contributors}
          logCount={planter.log_count}
          contributorCount={planter.contributor_count}
          lougeContent={planter.louge_content}
          planterId={planter.id}
          isFollowing={planter.is_following}
          loading={contributorsLoading}
        />,
      );
    } else {
      setContent(
        <ScoreCard
          status={planter.status}
          logCount={planter.log_count}
          contributorCount={planter.contributor_count}
          progress={planter.progress}
          scorePending={scorePending || bloomPending}
        />,
      );
    }
    return () => setContent(null);
  }, [
    planter.status,
    planter.log_count,
    planter.contributor_count,
    planter.progress,
    planter.louge_content,
    scorePending,
    bloomPending,
    contributors,
    contributorsLoading,
    isLouge,
    setContent,
  ]);

  const handleLogCreated = useCallback(
    (response: {
      log: {
        id: string;
        planter_id: string;
        user: {
          id: string;
          display_name: string;
          avatar_url: string | null;
        } | null;
        body: string;
        parent_log_id: string | null;
        is_ai_generated: boolean;
        created_at: string;
      };
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

      // Suppress unread bump from the Realtime echo of our own post. Bound
      // memory growth: if the echo never arrives (channel drop, backgrounded
      // tab, network loss), drop the id after 5 minutes so the Set cannot
      // grow unbounded over a long session. There is also a tiny race where
      // the echo lands BEFORE this add — see handleRealtimeLogInsert below.
      const ownPostId = response.log.id;
      ownPostIdsRef.current.add(ownPostId);
      window.setTimeout(() => {
        ownPostIdsRef.current.delete(ownPostId);
      }, 5 * 60 * 1000);

      // Append silently. We deliberately do NOT auto-scroll on post — the
      // user's scroll position is sacrosanct. If the user is currently
      // pinned to the bottom, the new log lands in view via the natural
      // sticky composer layout. If they're scrolled up, their own post
      // appends below the viewport and stays out of sight; we still skip
      // the unread bump (own posts never trigger the jump-to-latest button).
      logThreadRef.current?.addLog(response.log);

      if (response.score_pending) {
        setScorePending(true);
        pollScore(0);
      }
    },
    [pollScore],
  );

  const handleReply = useCallback(
    (logId: string) => {
      setReplyTo({ id: logId, displayName: "Log" });
    },
    [],
  );

  // A log just got committed by *anyone* (other user, AI, or echo of our
  // own post) — show "calculating" until the planter UPDATE Realtime brings
  // back the new score. Also drives the unreadCount used by the
  // jump-to-latest button: echoes of the current user's own posts are
  // filtered out via ownPostIdsRef.
  //
  // Tiny race: an echo for the user's own post can arrive on the WebSocket
  // BEFORE the POST response resolves — i.e. before handleLogCreated has run
  // ownPostIdsRef.add(). In that window the echo is treated as a stranger's
  // log. Mitigated by handleLogCreated also forcing isAtBottomRef.current =
  // true and clearing unreadCount, so as long as the user is actively
  // posting, an out-of-order echo cannot leave a stale unread badge.
  const handleRealtimeLogInsert = useCallback((row: RealtimeLogRow) => {
    setScorePending(true);
    if (ownPostIdsRef.current.has(row.id)) {
      ownPostIdsRef.current.delete(row.id);
      return;
    }
    if (!isAtBottomRef.current) {
      setUnreadCount((c) => c + 1);
    }
  }, []);

  const handleAtBottomChange = useCallback((atBottom: boolean) => {
    isAtBottomRef.current = atBottom;
    if (atBottom) {
      setUnreadCount(0);
    }
  }, []);

  const handleJumpToLatest = useCallback(() => {
    logThreadRef.current?.scrollToBottom("smooth");
    setUnreadCount(0);
  }, []);

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
          <Link
            href={`/user/${planter.user.id}`}
            className="hover:text-primary hover:underline"
          >
            {planter.user.display_name}
          </Link>
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

        {/* Louge state: Article view */}
        {isLouge && !bloomPending && planter.louge_content ? (
          <>
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

            {/* Divider */}
            <div className="mb-5 h-px bg-border" />

            {/* Louge article */}
            <LougeArticle
              content={planter.louge_content}
              generatedAt={planter.louge_generated_at!}
            />

            {/* Collapsible original Seed */}
            <div className="mb-5 rounded-lg bg-bg-page" data-testid="seed-collapsible">
              <button
                className="flex w-full items-center justify-between px-4 py-3 text-left"
                onClick={() => setSeedExpanded(!seedExpanded)}
                data-testid="seed-collapsible-toggle"
              >
                <span className="text-[13px] text-text-muted">
                  元のSeed（投稿者: {planter.user.display_name}）
                </span>
                <span className="text-[12px] text-primary">
                  {seedExpanded ? (
                    <span className="flex items-center gap-0.5">
                      <ChevronDown size={14} /> 閉じる
                    </span>
                  ) : (
                    <span className="flex items-center gap-0.5">
                      <ChevronRight size={14} /> 展開する
                    </span>
                  )}
                </span>
              </button>
              {seedExpanded && (
                <div className="px-4 pb-4">
                  <p className="whitespace-pre-wrap text-[13px] leading-[1.7] text-text-secondary">
                    {planter.body}
                  </p>
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="mb-5 h-px bg-border" />

            {/* Logs section (read-only) */}
            <h2 className="mb-4 text-heading-m text-primary-dark">Logs</h2>
            <LogThread
              ref={logThreadRef}
              planterId={planter.id}
              onReply={handleReply}
              onRealtimeInsert={handleRealtimeLogInsert}
              onAtBottomChange={handleAtBottomChange}
            />
          </>
        ) : isLouge && bloomPending ? (
          /* Bloom pending state */
          <div
            className="flex flex-col items-center justify-center py-20"
            data-testid="bloom-pending"
          >
            <div className="mb-4 animate-pulse">
              <Flower2 size={48} strokeWidth={1} className="text-primary" />
            </div>
            <p className="mb-1 text-[15px] font-medium text-primary-dark">
              開花中...
            </p>
            <p className="text-[13px] text-text-muted">
              記事を生成しています
            </p>
            {bloomTimedOut && (
              <p className="mt-4 text-[12px] text-text-muted">
                記事生成に時間がかかっています。しばらく後にもう一度アクセスしてください。
              </p>
            )}
          </div>
        ) : (
          /* Seed/Sprout state (existing) */
          <>
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
            <div className="mb-5 flex items-center gap-3 text-body-s text-text-muted">
              <span className="flex items-center gap-1">
                <MessageSquare size={14} strokeWidth={1.5} />
                {planter.log_count} logs
              </span>
              <span className="flex items-center gap-1">
                <Users size={14} strokeWidth={1.5} />
                {planter.contributor_count} contributors
              </span>
              <PlanterFollowButton
                planterId={planter.id}
                initialIsFollowing={planter.is_following}
              />
            </div>

            {/* Divider */}
            <div className="mb-5 h-px bg-border" />

            {/* Logs section */}
            <h2 className="mb-4 text-heading-m text-primary-dark">Logs</h2>
            <LogThread
              ref={logThreadRef}
              planterId={planter.id}
              onReply={handleReply}
              onRealtimeInsert={handleRealtimeLogInsert}
              onAtBottomChange={handleAtBottomChange}
            />
          </>
        )}
      </div>

      {/* Bottom sticky input bar (hidden for louge status) */}
      <LogComposer
        planterId={planter.id}
        planterStatus={planter.status}
        replyTo={replyTo}
        onCancelReply={() => setReplyTo(null)}
        onLogCreated={handleLogCreated}
        topOverlay={
          unreadCount > 0 ? (
            <button
              onClick={handleJumpToLatest}
              className="absolute -top-12 left-1/2 flex -translate-x-1/2 items-center gap-1 rounded-full bg-primary px-4 py-2 text-[13px] font-medium text-white shadow-lg transition-colors hover:bg-primary/90"
              data-testid="log-jump-to-latest"
            >
              <span>最新のLog</span>
              <ChevronDown size={14} />
            </button>
          ) : null
        }
      />
    </div>
  );
}
