import type { Metadata } from "next";
import { DM_Sans, DM_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import ErrorBoundary from "@/components/ErrorBoundary";

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans" });
const dmMono = DM_Mono({ subsets: ["latin"], weight: ["400"], variable: "--font-dm-mono" });

export const metadata: Metadata = {
  title:       "Analytiq — AI Analytics Platform",
  description: "Turn any dataset into client-ready insights with AutoML, SHAP explainability, and professional reports.",
  keywords:    ["analytics", "AutoML", "data science", "AI", "dashboard"],
  openGraph: {
    title:       "Analytiq — AI Analytics Platform",
    description: "Upload any CSV. Get ML predictions, AI narratives, and client-ready reports.",
    type:        "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${dmSans.variable} ${dmMono.variable} font-sans bg-gray-50 text-gray-900`}>
        <ErrorBoundary>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
