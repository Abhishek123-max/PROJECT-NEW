'use client';
import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
/* import Button from '@/components/ui/Button'; */
import Sidebar from "@/components/sidemenu/Sidebar";
import { Poppins } from "next/font/google";
import Header from "@/components/header/Header";

const poppins = Poppins({ subsets: ["latin"], weight: ["400", "600", "700"] });

export default function AdminDashboardPage() {
  const { theme } = useTheme();

  return (
    <div className={`${poppins.className} flex`}>
      {/* Sidebar */}
      <Sidebar />

      {/* Page content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <Header />

        {/* Main content */}
        <main className="flex-1 bg-gray-50 p-6">
          <div className="max-w-6xl mx-auto">
            <div className="rounded-xl bg-white shadow p-8 min-h-[320px] flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold mb-2" style={{ color: theme.text }}>Dashboard</h1>
                <p className="text-gray-500">Your admin dashboard is ready. Add widgets here.</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}


