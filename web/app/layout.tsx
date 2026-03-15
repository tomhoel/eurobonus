import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Nav } from "@/components/nav";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });

export const metadata: Metadata = {
  title: "hellasus.no — SAS EuroBonus Award Search",
  description: "Find SAS EuroBonus bonus ticket availability. Real-time search, smart alerts, best deals.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${geist.variable} ${geistMono.variable}`}>
      <body
        className="antialiased"
        style={{
          fontFamily: "var(--font-geist), -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          backgroundColor: "#000",
          color: "#ededed",
        }}
      >
        <Providers>
          <Nav />
          <main>{children}</main>
        </Providers>
      </body>
    </html>
  );
}
