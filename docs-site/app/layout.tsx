import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dividend API Documentation",
  description: "Production-grade API for dividend investors",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.Node;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
