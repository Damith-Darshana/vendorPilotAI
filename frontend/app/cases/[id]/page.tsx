// app/cases/[id]/page.tsx
import { getCase } from "@/lib/api";
import ClientPdfViewer from "@/components/ClientPdfViewer";

export const instant = false; 

export default async function CasePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const caseData = await getCase(id);

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-xl text-red-400 font-bold mb-2">{caseData.supplier_name}</h1>
      <p className="text-sm text-red-700 mb-6">
        Status: <span className="font-mono">{caseData.status}</span> | Case: {caseData.case_id}
      </p>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Findings */}
        <div>
          <h2 className="text-lg font-semibold mb-3">Findings</h2>
          {caseData.findings.length === 0 ? (
            <p className="text-gray-500">No findings.</p>
          ) : (
            <ul className="space-y-3">
              {caseData.findings.map((f) => (
                <li
                  key={f.id}
                  className="border rounded p-3 bg-gray-50"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded ${
                        f.severity === "critical"
                          ? "bg-red-100 text-red-700"
                          : f.severity === "high"
                          ? "bg-orange-100 text-orange-700"
                          : "bg-yellow-100 text-yellow-700"
                      }`}
                    >
                      {f.severity.toUpperCase()}
                    </span>
                    <span className="font-mono text-xs text-gray-600">{f.rule_id}</span>
                  </div>
                  <p className="text-sm">{f.message}</p>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Right: PDF Viewer */}
        <div>
          <h2 className="text-lg font-semibold mb-3">Document</h2>
          <ClientPdfViewer caseId={caseData.case_id} />
        </div>
      </div>
    </main>
  );
}