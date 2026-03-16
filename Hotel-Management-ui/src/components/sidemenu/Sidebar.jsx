"use client";
import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Logo } from "@/assests/svgicons";
import { useTheme } from "@/contexts/ThemeContext";
import {
  DashboardIcon,
  UsersIcon,
  HotelIcon,
  MenuIcon,
  BillingIcon,
  ReportsIcon,
  SettingsIcon,
  InventoryIcon,
  OrderIcon,
  DotsIcon,
  CaretUpIcon,
  CaretDownIcon,
} from "@/assests/icons";

const Sidebar = () => {
  const { theme } = useTheme();
  const pathname = usePathname();
  const router = useRouter();

  // Store multiple open categories
  const [openCategories, setOpenCategories] = useState([]);

  const menu = [
    {
      category: "Dashboard",
      path: "/dashboard",
      icon: <DashboardIcon width={26} height={26} />,
    },
    {
      category: "Employees & Roles",
      icon: <UsersIcon width={26} height={26} />,
      subItems: [
        {
          name: "Role Management",
          icon: <DotsIcon width={35} height={35} />,
          path: "/role-management/role",
        },
        {
          name: "Employees",
          icon: <DotsIcon width={35} height={35} />,
          path: "/role-management/employees",
        },
      ],
    },
    {
      category: "Hotel Management",
      icon: <HotelIcon width={26} height={26} />,
      subItems: [
        {
          name: "Hotel Branches",
          icon: <DotsIcon width={35} height={35} />,
          path: "/hotel-management/branches",
        },
        {
          name: "Table Management",
          icon: <DotsIcon width={35} height={35} />,
          path: "/hotel-management/table-management",
        },
      ],
    },
    {
      category: "Menu Management",
      icon: <MenuIcon width={26} height={26} />,
      subItems: [
        {
          name: "Kitchen Counter",
          icon: <DotsIcon width={35} height={35} />,
          path: "/kitchen",
        },
        {
          name: "Menu Items",
          icon: <DotsIcon width={35} height={35} />,
          path: "/items",
        },
        {
          name: "Settings",
          icon: <DotsIcon width={35} height={35} />,
          path: "/menu-settings",
        },
      ],
    },
    {
      category: "Billing Management",
      path: "/billing",
      icon: <BillingIcon width={24} height={24} />,
    },
    {
      category: "Orders",
      path: "/orders",
      icon: <OrderIcon width={26} height={26} />,
    },
    {
      category: "Inventory Management",
      path: "/inventory",
      icon: <InventoryIcon width={26} height={26} />,
    },
    {
      category: "Reports & Analytics",
      path: "/reports",
      icon: <ReportsIcon width={26} height={26} />,
    },
    {
      category: "Settings",
      path: "/settings",
      icon: <SettingsIcon width={26} height={26} />,
    },
  ];

  const handleCategoryClick = (item) => {
    if (item.subItems) {
      if (openCategories.includes(item.category)) {
        // Close the category if it's already open
        setOpenCategories(openCategories.filter((c) => c !== item.category));
      } else {
        // Open the category while keeping others open
        setOpenCategories([...openCategories, item.category]);
      }

      // Navigate to first sub-item if current path is different
      if (pathname !== item.subItems[0].path) {
        router.push(item.subItems[0].path);
      }
    }
  };

  return (
    <div className="h-screen w-64 border-r border-gray-100 flex flex-col">
      {/* Logo */}
      <div className="py-4 px-2 flex items-center mb-[15px]">
        <Logo className="h-12 w-12" />
      </div>

      {/* Menu */}
      <div className="flex-1 overflow-y-auto space-y-[20px]">
        {menu.map((item, index) => {
          const isParentActive =
            item.subItems?.some((sub) => pathname.startsWith(sub.path)) ||
            pathname === item.path;

          return (
            <div key={index}>
              {item.subItems ? (
                <>
                  {/* Category with Submenu */}
                  <div
                    onClick={() => handleCategoryClick(item)}
                    className={`py-[16px] px-2 pl-[32px] cursor-pointer flex justify-between items-center transition-colors 
                    ${
                      isParentActive
                        ? "bg-green-600 text-white"
                        : "text-[#1b1b1b] hover:bg-green-600 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-[10px] text-[14px] font-medium leading-[100%]">
                      {item.icon}
                      {item.category}
                    </div>
                    {openCategories.includes(item.category) ? (
                      <CaretUpIcon width={20} height={20} />
                    ) : (
                      <CaretDownIcon width={20} height={20} />
                    )}
                  </div>

                  {/* Submenu */}
                  {openCategories.includes(item.category) && (
                    <ul className="pl-8 mt-2 space-y-1">
                      {item.subItems.map((sub, idx) => (
                        <li key={idx}>
                          <Link
                            href={sub.path}
                            className={`flex items-center gap-3 px-2 rounded-md transition-colors cursor-pointer text-[14px] font-medium
            ${
              pathname.startsWith(sub.path)
                ? "text-green-600 font-semibold"
                : "text-[#1b1b1b]"
            }`}
                          >
                            <span className="flex items-center justify-center flex-shrink-0">
                              {sub.icon}
                            </span>
                            <span className="truncate mt-4">{sub.name}</span>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              ) : (
                <Link
                  href={item.path}
                  className={`flex items-center gap-[10px] px-3 py-[16px] pl-[32px] cursor-pointer transition-colors text-[14px] font-medium leading-[100%]
                  ${
                    pathname === item.path
                      ? "bg-green-600 text-white"
                      : "text-[#1b1b1b] hover:bg-green-600 hover:text-white"
                  }`}
                >
                  {item.icon}
                  <span>{item.category}</span>
                </Link>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Sidebar;
