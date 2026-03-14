import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import {
  getUserNotifications,
  markNotificationRead,
} from "@/lib/db/queries/notifications";

export async function GET() {
  const session = await auth();
  if (!session?.user?.id)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const items = await getUserNotifications(session.user.id);
  return NextResponse.json({ notifications: items });
}

export async function PATCH(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const { id } = await req.json();
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
  await markNotificationRead(id, session.user.id);
  return NextResponse.json({ ok: true });
}
