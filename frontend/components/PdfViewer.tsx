"use client";

import { useState } from "react";
import { Document,Page,pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Required worker configuration
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PdfViewerProps {
  caseId: string;
  targetPage?: number;
}

export default function PdfViewer({ caseId, targetPage }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(targetPage || 1);

  const fileUrl = `http://localhost:8000/api/v1/cases/${caseId}/document`;

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  return (
    <div className="border rounded p-4 bg-gray-50">
      <div className="flex items-center gap-2 mb-3">
        <button
          disabled={pageNumber <= 1}
          onClick={() => setPageNumber((p) => p - 1)}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          Prev
        </button>
        <span className="text-sm">
          Page {pageNumber} / {numPages || "?"}
        </span>
        <button
          disabled={pageNumber >= numPages}
          onClick={() => setPageNumber((p) => p + 1)}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>

      <Document
        file={fileUrl}
        onLoadSuccess={onDocumentLoadSuccess}
        onLoadError={(err) => console.error("PDF load error:", err)}
        loading={<p className="text-gray-500">Loading PDF...</p>}
        error={<p className="text-red-500">Failed to load PDF. Check backend endpoint.</p>}
      >
        <Page pageNumber={pageNumber} width={500} />
      </Document>
    </div>
  );
}