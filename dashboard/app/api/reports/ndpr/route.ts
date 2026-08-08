import { NextRequest, NextResponse } from "next/server";
import { getNdprReport } from "@/lib/server-api";

export const dynamic = "force-dynamic";

// One-click NDPR export: fetches the live compliance report from the VERDANT
// API (server-side, with the VERDANT key) and returns it as a downloadable
// JSON file. Linked from the Reports page "Download" button.
export async function GET(request: NextRequest) {
  const daysParam = Number(request.nextUrl.searchParams.get("days") ?? "30");
  const days = Number.isFinite(daysParam) && daysParam > 0 ? Math.min(daysParam, 365) : 30;

  const result = await getNdprReport(days);
  if (!result.ok) {
    const status = result.reason === "unconfigured" ? 503 : 502;
    return NextResponse.json(
      { error: result.reason === "unconfigured" ? "VERDANT_API_KEY not configured" : result.message },
      { status },
    );
  }

  const filename = `verdant-ndpr-report-${new Date().toISOString().slice(0, 10)}.json`;
  return new NextResponse(JSON.stringify(result.data, null, 2), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Cache-Control": "no-store",
    },
  });
}
