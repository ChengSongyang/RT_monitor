import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8001";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    
    const response = await fetch(`${API_BASE_URL}/api/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to refresh data:", error);
    return NextResponse.json(
      { error: "Failed to refresh data" },
      { status: 500 }
    );
  }
}
