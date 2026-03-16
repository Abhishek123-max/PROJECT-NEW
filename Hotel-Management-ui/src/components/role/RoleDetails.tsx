"use client";

import React, { useState } from "react";
import { InfoIcon } from "@/assests/icons";
import { Role } from "@/types/roles"; // 👈 import your role type

interface RoleDetailsProps {
  role: Role;
}

const RoleDetails: React.FC<RoleDetailsProps> = ({ role }) => {
  const [activeTab, setActiveTab] = useState<"Staff Assigned" | "Permissions">(
    "Staff Assigned"
  );

  // Temporary placeholder for assigned staff (until API adds it)
  const staff = ["Sujith", "Aarav", "Rohan", "Vikram", "Siddharth", "Kunal"];

  const getInitials = (name: string) =>
    name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase();

  const getBackgroundColor = (name: string) => {
    const colors = [
      "bg-purple-200 text-purple-800",
      "bg-teal-200 text-teal-800",
      "bg-blue-200 text-blue-800",
      "bg-green-200 text-green-800",
      "bg-yellow-200 text-yellow-800",
      "bg-red-200 text-red-800",
      "bg-orange-200 text-orange-800",
      "bg-pink-200 text-pink-800",
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colors.length;
    return colors[index];
  };

  return (
    <div className="space-y-6">
      {/* Role Info */}
      <div className="space-y-3 text-sm text-gray-600">
        <div className="flex justify-between">
          <span>Role</span>
          <span className="font-medium text-black text-[14px] font-[600]">
            {role.display_name}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Assigned Staff Count</span>
          <span className="font-medium text-black text-[14px] font-[600]">
            {staff.length}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Permissions</span>
          <span className="font-medium text-black text-[14px] font-[600]">
            {Object.keys(role.permissions || {}).length}
          </span>
        </div>
      </div>

      <hr className="border-t border-[#ECECEC] my-2" />

      {/* Description */}
      <div className="rounded-md flex flex-col gap-[7px] mt-3">
        <div className="flex flex-row gap-3">
          <InfoIcon width={21} height={21} color="#2FAC3E" />
          <h4 className="text-[14px] font-[600]">Description</h4>
        </div>

        <div className="h-14 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
          <p className="font-[400] text-[14px]">
            {role.description || "No description provided."}
          </p>
        </div>
      </div>

      <hr className="border-t border-[#ECECEC] my-2" />

      {/* Tabs */}
      <div className="flex">
        {["Staff Assigned", "Permissions"].map((tab) => (
          <button
            key={tab}
            className={`px-4 py-2 text-[14px] font-[600] cursor-pointer ${
              activeTab === tab
                ? "border-b-2 border-[#2FAC3E] text-[#0e0e0e]"
                : "text-[#adabb8]"
            }`}
            onClick={() =>
              setActiveTab(tab as "Staff Assigned" | "Permissions")
            }
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Staff Tab */}
      {activeTab === "Staff Assigned" && (
        <div className="flex flex-wrap gap-2 mt-4">
          {staff.length > 0 ? (
            staff.map((name, index) => (
              <div
                key={index}
                className="flex items-center space-x-2 p-2 rounded-[10px] border border-[#E9e9e9] bg-[#f6f6f6]"
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${getBackgroundColor(
                    name
                  )}`}
                >
                  {getInitials(name)}
                </div>
                <span className="text-[14px] text-[#00000]">{name}</span>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-sm mt-2">No staff assigned.</p>
          )}
        </div>
      )}

      {/* Permissions Tab */}
      {activeTab === "Permissions" && (
        <div className="mt-4 text-sm text-gray-700 space-y-2">
          {role.permissions ? (
            Object.entries(role.permissions).map(([module, perms]) => (
              <div key={module} className="border-b pb-2">
                <h4 className="font-semibold capitalize text-[#17181A] text-[14px]">
                  {module.replace(/([A-Z])/g, " $1")}
                </h4>
                <div className="flex flex-wrap gap-3 mt-1 ml-2 text-[13px] text-gray-600">
                  {Object.entries(perms)
                    .filter(([, allowed]) => allowed)
                    .map(([perm]) => (
                      <span key={perm} className="bg-[#E9F9EE] px-2 py-1 rounded-md text-[#2FAC3E]">
                        {perm}
                      </span>
                    ))}
                  {!Object.values(perms).some(Boolean) && (
                    <span className="text-gray-400">No active permissions</span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p>No permissions data available.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default RoleDetails;
