import Link from "next/link";
import UploadCase from "@/components/UploadCase";
import { Suspense } from "react";

interface CaseSummary {
  case_id: string;
  supplier_name: string;
  status: string;
  created_at: string;
}

async function fetchCases(): Promise<CaseSummary[]> {
  try {
    const res = await fetch("http://localhost:8000/api/v1/cases", {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

// Separate component to handle the async data fetch, wrapped by Suspense
async function CaseList() {
  const cases = await fetchCases();

  if (cases.length === 0) {
    return <p className="text-gray-500">No cases yet. Upload one to get started.</p>;
  }

  return (
    <ul className="space-y-2">
      {cases.map((c) => (
        <li key={c.case_id}>
          <Link
            href={`/cases/${c.case_id}`}
            className="block border rounded p-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{c.supplier_name}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded ${
                  c.status === "approved"
                    ? "bg-green-100 text-green-700"
                    : c.status === "rejected"
                    ? "bg-red-100 text-red-700"
                    : "bg-yellow-100 text-yellow-700"
                }`}
              >
                {c.status}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {c.case_id} · {new Date(c.created_at).toLocaleString()}
            </p>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default function Dashboard() {
  return (
    <main className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">VendorPilot Dashboard</h1>

      <div className="grid grid-cols-3 gap-8">
        {/* Upload form */}
        <div className="col-span-1">
          <UploadCase />
        </div>

        {/* Case list wrapped in Suspense to satisfy Next.js 16 caching/streaming rules */}
        <div className="col-span-2">
          <h2 className="text-lg font-semibold mb-3">Cases</h2>
          <Suspense fallback={<p className="text-gray-500">Loading cases...</p>}>
            <CaseList />
          </Suspense>
        </div>
      </div>
    </main>
  );
}