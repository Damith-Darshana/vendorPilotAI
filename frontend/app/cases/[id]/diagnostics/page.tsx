import Link from "next/link";

interface Metrics {
  provider: string;
  model_name: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
}

async function fetchMetrics(caseId: string): Promise<Metrics | null> {
  // First, get the job_id for this case
  const jobsRes = await fetch(
    `http://localhost:8000/api/v1/jobs/by-case/${caseId}`,
    { cache: "no-store" }
  );
  if (!jobsRes.ok) return null;
  const job = await jobsRes.json();

  const metricsRes = await fetch(
    `http://localhost:8000/api/v1/jobs/${job.job_id}/metrics`,
    { cache: "no-store" }
  );
  if (!metricsRes.ok) return null;
  return metricsRes.json();
}

export default async function DiagnosticsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const metrics = await fetchMetrics(id);

  return (
    <main className="p-8 max-w-3xl mx-auto">
      <Link href={`/cases/${id}`} className="text-blue-600 text-sm hover:underline">
        ← Back to case
      </Link>

      <h1 className="text-2xl font-bold mt-4 mb-6">Workflow Diagnostics</h1>

      {!metrics ? (
        <p className="text-gray-500">No metrics available for this case.</p>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="border rounded p-4">
            <p className="text-sm text-gray-500">Provider</p>
            <p className="font-mono text-lg">{metrics.provider}</p>
          </div>
          <div className="border rounded p-4">
            <p className="text-sm text-gray-500">Model</p>
            <p className="font-mono text-lg">{metrics.model_name ?? "N/A"}</p>
          </div>
          <div className="border rounded p-4">
            <p className="text-sm text-gray-500">Input Tokens</p>
            <p className="font-mono text-lg">{metrics.input_tokens ?? "N/A"}</p>
          </div>
          <div className="border rounded p-4">
            <p className="text-sm text-gray-500">Output Tokens</p>
            <p className="font-mono text-lg">{metrics.output_tokens ?? "N/A"}</p>
          </div>
          <div className="border rounded p-4">
            <p className="text-sm text-gray-500">Total Tokens</p>
            <p className="font-mono text-lg">{metrics.total_tokens ?? "N/A"}</p>
          </div>
          <div className="border rounded p-4">
            <p className="text-sm text-gray-500">Latency</p>
            <p className="font-mono text-lg">
              {metrics.latency_ms ? `${metrics.latency_ms} ms` : "N/A"}
            </p>
          </div>
        </div>
      )}
    </main>
  );
}