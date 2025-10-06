import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "reactflow/dist/style.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Generative Storyteller",
  description: "Story is our only boat for sailing on the river of time. - Ursula K. Le Guin",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
