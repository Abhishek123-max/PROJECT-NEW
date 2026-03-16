"use client";

import React, { useState } from "react";
import ActionDropdown from "../actiondropdown/ActionDropdown";
import Button from "../ui/Button";
import Drawer from "../ui/Drawer";
import HotelDetails from "@/components/hotel/HotelDeatails";
import Image from "next/image";
import hotel from "@/assests/hotel-logo.png";

const BranchCard = ({ branch }) => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleViewDetails = () => {
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
  };

  return (
    <>
      <div className="bg-white rounded-[10px] border border-[#e9e9e9] py-[14px] relative flex flex-col gap-[10px]">
        <div className="flex items-center px-[15px] ">
          {/* Branch Logo */}
          <div className="w-[68px] h-[68px] bg-gray-200 rounded-full mr-3 flex items-center justify-center">
            <Image
              src={hotel}
              alt="Hotel Empire Logo"
              className="rounded-full"
            />
          </div>

          {/* Branch Info */}
          <div className="flex-1">
            <h2 className="text-[16px] font-[700] text-[#0e0e0e]">
              {branch.name}
            </h2>
            <p className="text-[#1c1c1c] text-[14px]">{branch.location}</p>
          </div>

          {/* Main Branch Label */}
          <div>
            {branch.isMain && (
              <span className="px-[12px] py-[3px] bg-[#A2ED75] rounded-[20px] text-[12px] text-[#2F620F]">
                Main Branch
              </span>
            )}
          </div>
        </div>

        {/* Branch Details */}
        <div className=" bg-[#F8FCF8] px-[15px] py-[13px]">
          <div className="flex justify-between text-[13px] text-[#1b1b1b] mb-1">
            <span>GST Number</span>
            <span>FSSAI License No.</span>
          </div>
          <div className="flex justify-between text-[14px] text-[#1c1c1c] font-[600]">
            <span >{branch.gstNumber}</span>
            <span>{branch.fssaiLicense}</span>
          </div>
        </div>

        {/* Manager Info */}
        <div className="flex items-center px-[15px]">
          <div className="w-[37px] h-[37px] bg-gray-200 rounded-full mr-3 flex items-center justify-center">
            <svg
              className="w-5 h-5 text-gray-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div>
            <p className="text-[14px] font-[600] mb-1 text-[#1c1c1c]">
              {branch.managerName}
            </p>
            <p className="text-[14px] text-[#1b1b1b]">{branch.managerPhone}</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center gap-2 px-[15px] mt-2">
          <Button
            variant="outline"
            size="large"
            onClick={handleViewDetails} // ✅ Opens drawer
            className="w-full h-[42px] whitespace-nowrap 
               !bg-transparent !border !border-[#16A34A] 
               !text-[#16A34A] font-medium rounded-[8px]"
          >
            View Details
          </Button>

          <div className="relative overflow-visible">
            <ActionDropdown
              onEdit={() => alert(`Edit branch: ${branch.name}`)}
              onDelete={() => alert(`Delete branch: ${branch.name}`)}
            />
          </div>
        </div>
      </div>

      {/* ✅ Drawer Component */}
      <Drawer
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        title="Hotel Details"
      >
        <HotelDetails />
      </Drawer>
    </>
  );
};

export default BranchCard;
