"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

interface ContributionDay {
  date: string;
  count: number;
}

interface ContributionGraphProps {
  userId: string;
}

const CELL_SIZE = 10;
const GAP = 3;
const ROWS = 7;

const LEVEL_COLORS = [
  "#edebe3", // 0
  "#c6e0da", // 1
  "#8cc4b5", // 2
  "#4d9e8c", // 3
  "#29736b", // 4
];

function getLevel(count: number, max: number): number {
  if (count === 0) return 0;
  if (max === 0) return 0;
  const ratio = count / max;
  if (ratio <= 0.25) return 1;
  if (ratio <= 0.5) return 2;
  if (ratio <= 0.75) return 3;
  return 4;
}

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export function ContributionGraph({ userId }: ContributionGraphProps) {
  const [data, setData] = useState<ContributionDay[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Tokyo";
    apiFetch<{ contributions: ContributionDay[] }>(
      `/api/v1/users/${userId}/contributions?tz=${encodeURIComponent(tz)}`,
    )
      .then((res) => setData(res.contributions))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return (
      <div className="h-[130px] animate-pulse rounded-lg border border-border bg-bg-card" />
    );
  }

  // Build 365-day grid
  const today = new Date();
  const dayMap = new Map(data.map((d) => [d.date, d.count]));
  const max = Math.max(...data.map((d) => d.count), 1);

  const days: { date: Date; count: number }[] = [];
  for (let i = 364; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    days.push({ date: d, count: dayMap.get(key) ?? 0 });
  }

  // Group into weeks (columns)
  const firstDay = days[0].date.getDay();
  const weeks: (typeof days)[] = [];
  let currentWeek: typeof days = [];

  // Pad first week
  for (let i = 0; i < firstDay; i++) {
    currentWeek.push({ date: new Date(0), count: -1 }); // placeholder
  }

  for (const day of days) {
    currentWeek.push(day);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }
  if (currentWeek.length > 0) {
    weeks.push(currentWeek);
  }

  const LABEL_W = 24;
  const gridWidth = weeks.length * (CELL_SIZE + GAP);
  const vbWidth = LABEL_W + gridWidth;
  const vbHeight = ROWS * (CELL_SIZE + GAP) + 20;

  // Month labels
  const monthLabels: { label: string; x: number }[] = [];
  let lastMonth = -1;
  weeks.forEach((week, wi) => {
    const validDay = week.find((d) => d.count >= 0);
    if (!validDay) return;
    const m = validDay.date.getMonth();
    if (m !== lastMonth) {
      lastMonth = m;
      monthLabels.push({ label: MONTHS[m], x: LABEL_W + wi * (CELL_SIZE + GAP) });
    }
  });

  const dayLabels: { label: string; row: number }[] = [
    { label: "Mon", row: 1 },
    { label: "Wed", row: 3 },
    { label: "Fri", row: 5 },
  ];

  return (
    <div data-testid="contribution-graph">
      <h3 className="mb-2 text-heading-m text-primary-dark">貢献グラフ</h3>
      <div className="rounded-lg border border-border bg-bg-card p-3">
        <svg
          viewBox={`0 0 ${vbWidth} ${vbHeight}`}
          preserveAspectRatio="xMidYMid meet"
          className="block w-full"
        >
          {/* Month labels */}
          {monthLabels.map((m, i) => (
            <text
              key={i}
              x={m.x}
              y={10}
              className="fill-text-muted text-[9px]"
              fontFamily="Inter, sans-serif"
            >
              {m.label}
            </text>
          ))}

          {/* Day-of-week labels */}
          {dayLabels.map((d) => (
            <text
              key={d.label}
              x={0}
              y={d.row * (CELL_SIZE + GAP) + 16 + CELL_SIZE - 1}
              className="fill-text-muted text-[9px]"
              fontFamily="Inter, sans-serif"
            >
              {d.label}
            </text>
          ))}

          {/* Cells */}
          {weeks.map((week, wi) =>
            week.map((day, di) => {
              if (day.count < 0) return null;
              const level = getLevel(day.count, max);
              return (
                <rect
                  key={`${wi}-${di}`}
                  x={LABEL_W + wi * (CELL_SIZE + GAP)}
                  y={di * (CELL_SIZE + GAP) + 16}
                  width={CELL_SIZE}
                  height={CELL_SIZE}
                  rx={2}
                  fill={LEVEL_COLORS[level]}
                >
                  <title>
                    {day.date.toISOString().slice(0, 10)}: {day.count}
                  </title>
                </rect>
              );
            }),
          )}
        </svg>

        {/* Legend */}
        <div className="mt-1 flex items-center justify-end gap-1 text-[9px] text-text-muted">
          <span>Less</span>
          {LEVEL_COLORS.map((c, i) => (
            <div
              key={i}
              className="h-[10px] w-[10px] rounded-[2px]"
              style={{ backgroundColor: c }}
            />
          ))}
          <span>More</span>
        </div>
      </div>
    </div>
  );
}
