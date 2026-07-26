import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/lib/theme-context";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Orpaq AI - Lead Generation Dashboard",
  description: "AI-powered business discovery and lead generation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <AuthProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
