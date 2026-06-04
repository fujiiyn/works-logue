export type PlanterDisplayShape = {
  status: string;
  title: string;
  logue_title?: string | null;
};

export function getDisplayTitle(planter: PlanterDisplayShape): string {
  if (planter.status === "logue" && planter.logue_title) {
    return planter.logue_title;
  }
  return planter.title;
}
