import { Suspense } from "react";
import { PlanterFeed } from "@/components/planter/PlanterFeed";

export default function HomePage() {
  return (
    <div data-testid="home-page">
      <Suspense>
        <PlanterFeed />
      </Suspense>
    </div>
  );
}
