import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "MA2 — Multi-Agent Action Planner",
  description: "Process meeting transcripts into reviewed action plans",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-ma2-50 text-ma2-900 min-h-screen">
        <nav className="bg-white border-b border-ma2-200">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14">
              <Link
                href="/"
                className="text-lg font-bold text-ma2-900 tracking-tight"
              >
                MA2
              </Link>
              <div className="flex items-center gap-6">
                <Link
                  href="/runs"
                  className="text-sm text-ma2-600 hover:text-ma2-900 transition-colors"
                >
                  Runs
                </Link>
                <Link
                  href="/runs/new"
                  className="text-sm text-ma2-600 hover:text-ma2-900 transition-colors"
                >
                  New Run
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
