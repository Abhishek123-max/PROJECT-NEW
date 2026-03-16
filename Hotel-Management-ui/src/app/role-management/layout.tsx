import React, { ReactNode } from "react";
import Sidebar from "@/components/sidemenu/Sidebar";
import Header from "@/components/header/Header";
import { Poppins } from "next/font/google";

const poppins = Poppins({ subsets: ["latin"], weight: ["400", "600", "700"] });

interface RoleLayoutProps {
  children: ReactNode;
}

const RoleLayout: React.FC<RoleLayoutProps> = ({ children }) => {
  return (
    <div className={`${poppins.className} flex`}>
      {/* Sidebar */}
      <Sidebar />

      {/* Page content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <Header />

        {/* Main content */}
        <main className="flex-1 bg-gray-50">{children}</main>
      </div>
    </div>
  );
};

export default RoleLayout;
