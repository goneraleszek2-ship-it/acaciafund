import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AcaciaFund",
  description: "Automated research synthesis and an experimental learning ecosystem.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-[100vh] flex flex-col">{children}</body>
    </html>
  );
}
