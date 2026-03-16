'use client';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';
import type { ReactNode } from 'react';
import { Poppins } from "next/font/google";
import '../app/globals.css';

const poppins = Poppins({ subsets: ["latin"], weight: ["400", "600", "700"] });


export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={poppins.className}>
      <body className="bg-shade-green min-h-screen">
        <ThemeProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}