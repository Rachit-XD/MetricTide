import { NextResponse } from "next/server";

/**
 * Liveness check for the web service.
 *
 * Trivial by design: proves routing and container startup work. It does not
 * call the API or check dependencies.
 */
export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({ status: "ok", service: "web" });
}
