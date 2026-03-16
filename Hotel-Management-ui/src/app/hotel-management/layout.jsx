import Sidebar from "@/components/sidemenu/Sidebar";
import { Poppins } from "next/font/google";
import Header from "@/components/header/Header"; 

const poppins = Poppins({ subsets: ["latin"], weight: ["400", "600", "700"] });

export default function HotelLayout({ children }) {
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
}
