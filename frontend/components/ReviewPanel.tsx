"use client";

import { useState } from "react";
import { submitDecision } from "@/lib/api";
import { useRouter } from "next/navigation";

interface ReviewPanelProps {
  caseId: string;
}

export default function ReviewPanel({ caseId }: ReviewPanelProps) {
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleDecision(decision: "approved" | "rejected") {
    setSubmitting(true);
    setError(null);
    try {
      await submitDecision(caseId, decision, notes || undefined);
      // Wait a moment for the backend to resume, then refresh the page
      setTimeout(() => router.refresh(), 1500);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="border rounded p-4 bg-yellow-50 mt-6">
      <h2 className="text-lg font-semibold mb-2">Human Review Required</h2>
      <p className="text-sm text-gray-700 mb-3">
        This case has been paused. Approve or reject it to resume the workflow.
      </p>

      <textarea
        className="w-full border rounded p-2 text-sm mb-3"
        rows={2}
        placeholder="Optional reviewer notes..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}

      <div className="flex gap-2">
        <button
          disabled={submitting}
          onClick={() => handleDecision("approved")}
          className="px-4 py-2 bg-green-600 text-white rounded text-sm disabled:opacity-50"
        >
          {submitting ? "Submitting..." : "Approve"}
        </button>
        <button
          disabled={submitting}
          onClick={() => handleDecision("rejected")}
          className="px-4 py-2 bg-red-600 text-white rounded text-sm disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </div>
  );
}