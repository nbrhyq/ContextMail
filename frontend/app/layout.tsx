import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ContextMail — Communication agent",
  description: "Plan, ground, review, and approve important emails.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
