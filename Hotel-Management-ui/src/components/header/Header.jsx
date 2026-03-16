"use client";
import { Bell, LogOut } from "lucide-react";
import Image from "next/image";
import { CaretDownIcon, CircleChevronDownIcon } from "@/assests/icons";
import SearchInput from "@/components/ui/SearchInput";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Header() {
  const [user, setUser] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Get user data from localStorage
    const getUserData = () => {
      try {
        const userData = localStorage.getItem("user");
        if (userData) {
          setUser(JSON.parse(userData));
        }
      } catch (error) {
        console.error("Error parsing user data:", error);
      }
    };

    getUserData();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest(".dropdown-container")) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showDropdown]);

  const handleLogout = async () => {
    setIsLoggingOut(true);

    try {
      // Simulate a brief delay to show loading state
      await new Promise((resolve) => setTimeout(resolve, 500));

      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");

      router.replace("/");
    } catch (error) {
      console.error("Error during logout:", error);
    } finally {
      setIsLoggingOut(false);
    }
  };
  return (
    <header className="h-[70px] px-[27px] py-[15px] bg-white flex items-center justify-between">
      <div className="flex items-center gap-4 w-1/2">
        <div className="flex items-center gap-3 cursor-pointer px-3 py-3 border border-gray-300 rounded-[10px]">
          <p className="text-sm">
            Kormangala-{" "}
            <span className="font-semibold text-gray-800">Empire Hotel</span>
          </p>
          <CaretDownIcon width={20} height={20} />
        </div>

        {/* Search Bar */}
        <div className="flex-1">
          <SearchInput
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Search"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-6">
        {/* Notifications */}
        <div className="relative">
          <Bell className="w-6 h-6 text-gray-600 cursor-pointer hover:text-black transition" />
          <span className="absolute -top-1 -right-2 bg-red-500 text-white text-xs font-semibold rounded-full px-1.5">
            3
          </span>
        </div>

        <div className="relative dropdown-container">
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => setShowDropdown(!showDropdown)}
          >
            <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-semibold">
              {user?.username?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex flex-col leading-tight">
              <h3 className="text-[14px] font-semibold text-gray-800">
                {user?.username || "User"}
              </h3>
              <span className="text-xs text-gray-500">
                {user?.role || "Admin"}
              </span>
            </div>
            <button className="p-1 rounded-full hover:bg-gray-100">
              <CircleChevronDownIcon width={17} height={17} color="gray" />
            </button>
          </div>

          {/* Dropdown Menu */}
          {showDropdown && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
              <div className="px-4 py-2 border-b border-gray-100">
                <p className="text-sm font-medium text-gray-800">
                  {user?.username || "User"}
                </p>
                <p className="text-xs text-gray-500">
                  {user?.email || "user@example.com"}
                </p>
              </div>
              <button
                onClick={handleLogout}
                disabled={isLoggingOut}
                className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 ${
                  isLoggingOut
                    ? "text-gray-400 cursor-not-allowed"
                    : "text-red-600 hover:bg-red-50"
                }`}
              >
                <LogOut className="w-4 h-4" />
                {isLoggingOut ? "Logging out..." : "Logout"}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
