import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MetricTide",
  description: "Discover emerging technology and startup trends before they go mainstream.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
