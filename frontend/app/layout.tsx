import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PayGuard",
  description: "AI-powered invoice & vendor verification for B2B payments",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
