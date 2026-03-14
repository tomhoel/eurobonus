import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import {
  getUserSubscriptions,
  createSubscription,
  deleteSubscription,
} from "@/lib/db/queries/subscriptions";

export async function GET() {
  const session = await auth();
  if (!session?.user?.id)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const subs = await getUserSubscriptions(session.user.id);
  return NextResponse.json({ subscriptions: subs });
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await req.json();
  const { origin, destination, cabinClass, dateFrom, dateTo } = body;

  if (!origin || !destination) {
    return NextResponse.json(
      { error: "origin and destination required" },
      { status: 400 },
    );
  }

  const sub = await createSubscription({
    userId: session.user.id,
    origin,
    destination,
    cabinClass: cabinClass ?? "any",
    dateFrom,
    dateTo,
  });

  return NextResponse.json({ subscription: sub }, { status: 201 });
}

export async function DELETE(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { id } = await req.json();
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });

  await deleteSubscription(id, session.user.id);
  return NextResponse.json({ ok: true });
}
