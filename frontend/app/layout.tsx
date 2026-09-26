import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://nbrhyq.github.io/ContextMail/"),
  title: "ContextMail — Your AI agent for important emails",
  description: "ContextMail understands, plans, drafts and verifies important emails before you send.",
  openGraph: {
    title: "ContextMail — AI Communication Agent",
    description: "From materials to ready-to-send emails, planned and verified before you send.",
    url: "https://nbrhyq.github.io/ContextMail/",
    siteName: "ContextMail",
    type: "website",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
