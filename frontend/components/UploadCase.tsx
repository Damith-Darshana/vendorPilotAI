"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";

type UploadState = "idle" | "uploading" | "processing" | "done" | "error";

export default function UploadCase() {
  const [state, setState] = useState<UploadState>("idle");
  const [supplierName, setSupplierName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleFile = useCallback((selected: File) => {
    if (selected.type !== "application/pdf") {
      setMessage("Only PDF files are accepted.");
      setState("error");
      return;
    }
    setFile(selected);
    setMessage("");
    setState("idle");
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const dropped = e.dataTransfer.files?.[0];
      if (dropped) handleFile(dropped);
    },
    [handleFile]
  );

  const onUpload = async () => {
    if (!file || !supplierName.trim()) {
      setMessage("Supplier name and a PDF file are required.");
      setState("error");
      return;
    }

    setState("uploading");
    setMessage("Uploading...");

    const formData = new FormData();
    formData.append("supplier_name", supplierName.trim());
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/v1/cases", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const { case_id, job_id } = data;

      setState("processing");
      setMessage("Processing document...");

      // Connect SSE stream
      const es = new EventSource(
        `http://localhost:8000/api/v1/jobs/${job_id}/stream`
      );

      console.log(`\n job id :${job_id} \n`);

      es.addEventListener("job_started", (e:MessageEvent) => {
        console.log("job Started Message--",e.data);
        setMessage("Extracting fields--");
      });
      es.addEventListener("progress",(e:MessageEvent)=>{
        console.log("SSE Progress : ",e.data);
        const data = JSON.parse(e.data);
        if (data.stage =="extracting")setMessage("Extracting fields...");
        if (data.stage == "validating") setMessage("Validating Rules...");
      });

      es.addEventListener("hitl_required", (e:MessageEvent) => {
        console.log("SSE hit1_required:",e.data);
        setMessage("Paused for human review. Redirecting...");
        es.close();
        router.push(`/cases/${case_id}`);
        router.refresh();
      });

      es.addEventListener("job_completed", (e:MessageEvent) => {
        setMessage("Completed. Redirecting...");
        es.close();
        router.push(`/cases/${case_id}`);
        router.refresh();
      });

      es.addEventListener("error", () => {
        // EventSource fires error on normal close too; only show if still processing
        if (state === "processing") {
          setMessage("Stream disconnected. Check the case page.");
          setState("error");
        }
        es.close();
      });

      // Safety timeout: if nothing happens in 60s, stop waiting
      setTimeout(() => {
        if (es.readyState !== EventSource.CLOSED) {
          es.close();
          setMessage("Taking longer than expected. Check the dashboard.");
          setState("error");
        }
      }, 120000);
    } catch (err: any) {
      setMessage(err.message || "Upload failed.");
      setState("error");
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Upload New Supplier Case</h2>

      <input
        type="text"
        placeholder="Supplier name (e.g., Apex Logistics Inc.)"
        value={supplierName}
        onChange={(e) => setSupplierName(e.target.value)}
        className="w-full border rounded p-2 mb-3 text-sm"
        disabled={state === "uploading" || state === "processing"}
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? "border-blue-400 bg-blue-50"
            : "border-gray-300 bg-gray-50 hover:border-blue-300"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
        {file ? (
          <p className="text-sm text-gray-700">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        ) : (
          <p className="text-sm text-gray-500">
            Drag & drop a PDF here, or click to browse
          </p>
        )}
      </div>

      {message && (
        <p
          className={`text-sm mt-3 ${
            state === "error" ? "text-red-600" : "text-blue-600"
          }`}
        >
          {message}
        </p>
      )}

      <button
        onClick={onUpload}
        disabled={state === "uploading" || state === "processing"}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {state === "uploading"
          ? "Uploading..."
          : state === "processing"
          ? "Processing..."
          : "Upload & Process"}
      </button>
    </div>
  );
}