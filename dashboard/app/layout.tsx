import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Lexend, Source_Sans_3 } from "next/font/google";
import "./globals.css";

const display = Lexend({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
});

const body = Source_Sans_3({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "VERDANT | Inspectable AI governance",
  description:
    "A lightweight, NDPR-native SDK that wraps AI calls and returns structured reasoning, bias flags, explanations, and a trust score.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} scroll-smooth`}>
      <body className="bg-slate-50 font-body text-slate-950 antialiased dark:bg-slate-950 dark:text-slate-50">
        {children}
      </body>
    </html>
  );
}
