import type { Metadata } from "next";
import MainLayout from "@/components/layout/MainLayout";
import "./globals.css";

export const metadata: Metadata = {
  title: "LifeOS",
  description:
    "LifeOS - the Agentic Execution Operating System. Turn goals into completed outcomes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="bg-background text-foreground flex min-h-full flex-col">
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
}
