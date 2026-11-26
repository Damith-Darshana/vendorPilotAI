import { Suspense } from "react";
import { getCase } from "@/lib/api";
import CaseWorkspace from "@/components/CaseWorkspace";

async function CaseContent({ id }: { id: string }) {
  const caseData = await getCase(id);

  return (
    <>
      <h1 className="text-2xl font-bold mb-2">{caseData.supplier_name}</h1>
      <p className="text-sm text-gray-500 mb-6">
        Status: <span className="font-mono">{caseData.status}</span> | Case: {caseData.case_id}
      </p>
      <CaseWorkspace
        caseId={caseData.case_id}
        findings={caseData.findings}
        jobStatus={caseData.job_status}
      />
    </>
  );
}

function CaseSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/4 mb-6"></div>
      <div className="grid grid-cols-2 gap-6">
        <div className="h-64 bg-gray-200 rounded"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    </div>
  );
}

export default async function CasePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <Suspense fallback={<CaseSkeleton />}>
        <CaseContent id={id} />
      </Suspense>
    </main>
  );
}