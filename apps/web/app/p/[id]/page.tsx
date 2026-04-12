import { notFound } from "next/navigation";
import { PlanterDetailClient } from "./planter-detail-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  diversity_score: number;
  structure_score: number;
  bloom_threshold: number;
  created_at: string;
}

async function fetchPlanter(id: string): Promise<PlanterDetail | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/planters/${id}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function PlanterDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const planter = await fetchPlanter(id);

  if (!planter) {
    notFound();
  }

  return <PlanterDetailClient planter={planter} />;
}
