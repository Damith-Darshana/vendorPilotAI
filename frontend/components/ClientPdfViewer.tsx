// components/ClientPdfViewer.tsx
"use client";

import dynamic from "next/dynamic";

const PdfViewer = dynamic(() => import("@/components/PdfViewer"), {
  ssr: false,
  loading: () => <p className="text-gray-500">Loading viewer...</p>,
});

export default function ClientPdfViewer({ caseId }: { caseId: string }) {
  return <PdfViewer caseId={caseId} />;
}