"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "./ui/Button";
import { Card, CardHeader, CardBody } from "./ui/Card";
import { createRun } from "@/lib/api";
import { SAMPLE_TRANSCRIPT, SAMPLE_RULES } from "@/lib/sample-data";

export function RunForm() {
  const router = useRouter();
  const [transcript, setTranscript] = useState("");
  const [rules, setRules] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoadSample = () => {
    setTranscript(SAMPLE_TRANSCRIPT);
    setRules(SAMPLE_RULES);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transcript.trim() || !rules.trim()) {
      setError("Both transcript and rules are required.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result = await createRun(transcript, rules);
      router.push(`/runs/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create run");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-ma2-900">New Run</h2>
            <Button type="button" variant="secondary" size="sm" onClick={handleLoadSample}>
              Load Sample Input
            </Button>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-5">
            <div>
              <label
                htmlFor="transcript"
                className="block text-sm font-medium text-ma2-700 mb-1.5"
              >
                Meeting Transcript
              </label>
              <textarea
                id="transcript"
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                rows={10}
                className="w-full rounded-lg border border-ma2-300 px-3 py-2 text-sm text-ma2-900 placeholder:text-ma2-400 focus:border-ma2-500 focus:outline-none focus:ring-1 focus:ring-ma2-500 resize-y"
                placeholder="Paste the meeting transcript here..."
              />
              <p className="mt-1 text-xs text-ma2-400">
                {transcript.length.toLocaleString()} / 50,000 characters
              </p>
            </div>

            <div>
              <label
                htmlFor="rules"
                className="block text-sm font-medium text-ma2-700 mb-1.5"
              >
                Company Rules
              </label>
              <textarea
                id="rules"
                value={rules}
                onChange={(e) => setRules(e.target.value)}
                rows={6}
                className="w-full rounded-lg border border-ma2-300 px-3 py-2 text-sm text-ma2-900 placeholder:text-ma2-400 focus:border-ma2-500 focus:outline-none focus:ring-1 focus:ring-ma2-500 resize-y"
                placeholder="Paste the company rules/policies here..."
              />
              <p className="mt-1 text-xs text-ma2-400">
                {rules.length.toLocaleString()} / 10,000 characters
              </p>
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="flex justify-end">
              <Button type="submit" disabled={isSubmitting} size="lg">
                {isSubmitting ? "Starting..." : "Start Run"}
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>
    </form>
  );
}
