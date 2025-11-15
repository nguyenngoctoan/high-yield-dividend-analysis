import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Divv API Documentation",
  description: "Production-grade dividend data API for investors and developers",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
