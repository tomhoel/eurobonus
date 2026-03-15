import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { DrizzleAdapter } from "@auth/drizzle-adapter";
import { db } from "./db";

const hasDB = !!process.env.DATABASE_URL;

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...(hasDB ? { adapter: DrizzleAdapter(db) } : {}),
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
    }),
  ],
  callbacks: {
    session({ session, user }) {
      if (session.user && user) session.user.id = user.id;
      return session;
    },
  },
  pages: {
    signIn: "/",
  },
});
