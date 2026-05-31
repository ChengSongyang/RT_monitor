import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://127.0.0.1:8001";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const kind = searchParams.get("kind");
  const sourceKind = searchParams.get("source_kind");
  const includeEmpty = searchParams.get("include_empty");
  const view = searchParams.get("view");

  try {
    if (view === "rss") {
      const response = await fetch(`${API_BASE_URL}/api/sources?view=rss`, {
        cache: "no-store",
      });
      const data = await response.json();

      return NextResponse.json(data, { status: response.status });
    }

    const params = new URLSearchParams();
    if (kind) params.append("kind", kind);
    if (sourceKind) params.append("source_kind", sourceKind);
    if (includeEmpty) params.append("include_empty", includeEmpty);

    const response = await fetch(`${API_BASE_URL}/api/sources?${params.toString()}`, {
      cache: "no-store",
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch sources:", error);
    return NextResponse.json(
      {
        sources: [],
        total_sources: 0,
        active_sources: 0,
        total_items: 0,
        source_kinds: {},
        catalog: { total_configured: 0, kind_labels: {}, configured_kinds: {} },
        recent_syncs: [],
        error: "Failed to fetch sources",
      },
      { status: 500 }
    );
  }
}
