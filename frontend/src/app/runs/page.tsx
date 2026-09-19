"use client";

import Link from "next/link";
import { RunList } from "@/components/RunList";
import { Button } from "@/components/ui/Button";

export default function RunsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-ma2-900">Runs</h1>
        <Link href="/runs/new">
          <Button>New Run</Button>
        </Link>
      </div>
      <RunList />
    </div>
  );
}
