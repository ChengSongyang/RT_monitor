import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8001";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get("category");
  const source = searchParams.get("source");
  const sourceType = searchParams.get("source_type");
  const sourceId = searchParams.get("source_id");
  const sourceKind = searchParams.get("source_kind");
  const search = searchParams.get("search");
  const isFeatured = searchParams.get("is_featured");
  const limit = searchParams.get("limit") || "20";
  const page = searchParams.get("page") || "1";

  try {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (source) params.append("source", source);
    if (sourceType) params.append("source_type", sourceType);
    if (sourceId) params.append("source_id", sourceId);
    if (sourceKind) params.append("source_kind", sourceKind);
    if (search) params.append("search", search);
    if (isFeatured) params.append("is_featured", isFeatured);
    params.append("limit", limit);
    params.append("page", page);

    const response = await fetch(`${API_BASE_URL}/api/items?${params.toString()}`, {
      cache: "no-store",
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch items:", error);
    return NextResponse.json(
      { items: [], total: 0, page: 1, totalPages: 1, limit: 20, error: "Failed to fetch items" },
      { status: 500 }
    );
  }
}
