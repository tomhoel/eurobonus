import { NextRequest, NextResponse } from "next/server";
import { getActiveSession, refreshSession } from "@/lib/sas/session";

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const current = await getActiveSession();
  if (current) {
    return NextResponse.json({ ok: true, status: "session still active" });
  }

  const success = await refreshSession();
  return NextResponse.json({ ok: success, status: success ? "refreshed" : "refresh failed" });
}
