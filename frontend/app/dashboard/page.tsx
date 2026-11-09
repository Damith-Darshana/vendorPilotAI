import Link from "next/link";

export default function Dashboard() {
  const sampleCaseId = "case_8505b965";

  return(
    <main className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">VendorPilot Dashboard</h1>
      <p className="text-gray-600 mb-4">
        Case list will appear here once the list endpoint is built.
      </p>
      <Link
        href={`/cases/${sampleCaseId}`}
        className="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Open Sample Case ({sampleCaseId})
      </Link>
    </main>
  );
}