import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AlphaSage — Investment Intelligence",
  description: "Understand your portfolio and the market with AlphaSage."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

