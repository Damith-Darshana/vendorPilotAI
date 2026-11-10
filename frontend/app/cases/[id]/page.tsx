import { getCase } from "@/lib/api";
import CaseWorkspace from "@/components/CaseWorkspace";

export default async function CasePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const caseData = await getCase(id);

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">{caseData.supplier_name}</h1>
      <p className="text-sm text-gray-500 mb-6">
        Status: <span className="font-mono">{caseData.status}</span> | Case: {caseData.case_id}
      </p>

      <CaseWorkspace
        caseId={caseData.case_id}
        findings={caseData.findings}
        jobStatus={caseData.job_status}
      />
    </main>
  );
}