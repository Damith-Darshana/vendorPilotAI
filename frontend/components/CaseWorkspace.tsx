"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Finding } from "@/lib/api";

const PdfViewer = dynamic(() => import("@/components/PdfViewer"), {
  ssr: false,
  loading: () => <p className="text-gray-500">Loading viewer...</p>,
});

interface CaseWorkspaceProps {
  caseId: string;
  findings: Finding[];
}

export default function CaseWorkspace({ caseId, findings }: CaseWorkspaceProps) {
  const [targetPage, setTargetPage] = useState<number | undefined>(undefined);

  const handleFindingClick = (pageNumber: number | null) => {
    if (pageNumber) {
      setTargetPage(pageNumber);
    }
  };

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Left: Findings */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Findings</h2>
        {findings.length === 0 ? (
          <p className="text-gray-500">No findings.</p>
        ) : (
          <ul className="space-y-3">
            {findings.map((f) => (
              <li
                key={f.id}
                onClick={() => handleFindingClick(f.page_number)}
                className={`border rounded p-3 bg-gray-50 ${
                  f.page_number ? "cursor-pointer hover:bg-gray-100" : ""
                }`}
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
                  {f.page_number && (
                    <span className="text-xs text-blue-600 ml-auto">
                      Page {f.page_number}
                    </span>
                  )}
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
        <PdfViewer caseId={caseId} targetPage={targetPage} />
      </div>
    </div>
  );
}