import { NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8001";

const fallback = {
  sources: [],
  total_sources: 0,
  enabled_sources: 0,
  active_sources: 0,
};

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/rss-sources`, {
      cache: "no-store",
    });
    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch RSS sources:", error);
    return NextResponse.json(
      {
        ...fallback,
        error: "Failed to fetch RSS sources",
      },
      { status: 500 }
    );
  }
}
