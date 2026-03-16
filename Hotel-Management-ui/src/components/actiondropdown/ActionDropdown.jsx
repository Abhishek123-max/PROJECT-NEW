"use client";

import React, { useState, useEffect, useRef } from "react";
import Button from "@/components/ui/Button";
import { OptionIcon } from "@/assests/icons";

const ActionDropdown = ({ row, onViewDetails, onEdit, onDelete }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const toggleDropdown = () => setIsOpen((prev) => !prev);

  const handleActionClick = (actionFn, ...args) => {
    actionFn?.(...args);
    setIsOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <Button
        onClick={toggleDropdown}
        className="!border !border-[#eff0f2] !bg-white cursor-pointer !p-1 rounded"
      >
        <OptionIcon width={30} height={30} color="#000" />
      </Button>

      {isOpen && (
        <div
          className="origin-top-right absolute right-0 w-[113px] rounded-md bg-white z-10 dropdown-menu"
          style={{
            boxShadow:
              "0px 6.4px 14.4px 0px #00000021, 0px 1.2px 3.6px 0px #0000001A",
          }}
        >
          <div className="py-1" role="menu">
            {/* Only render buttons if the corresponding prop exists */}
            {onViewDetails && (
              <Button
                size="small"
                onClick={() => handleActionClick(onViewDetails, row)}
                className="flex justify-start w-full !bg-white !text-gray-700 hover:bg-gray-100 cursor-pointer"
              >
                View Details
              </Button>
            )}
            {onEdit && (
              <Button
                size="small"
                onClick={() => handleActionClick(onEdit, row)}
                className="flex justify-start w-full !bg-white !text-gray-700 hover:bg-gray-100 cursor-pointer"
              >
                Edit
              </Button>
            )}
            {onDelete && (
              <Button
                size="small"
                onClick={() => handleActionClick(onDelete, row)}
                className="flex justify-start w-full !bg-white !text-[#ff6f66] hover:bg-gray-100 cursor-pointer"
              >
                Delete
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ActionDropdown;
