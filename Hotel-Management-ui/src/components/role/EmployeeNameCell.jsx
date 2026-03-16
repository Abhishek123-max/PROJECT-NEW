"use client";
import React, { useState } from "react";

const EmployeeNameCell = ({ name }) => {
  const [isHovered, setIsHovered] = useState(false);
  const maxLength = 13;

  const displayName =
    name.length > maxLength ? name.substring(0, maxLength) + "..." : name;

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span className="cursor-pointer font-medium text-gray-800">
        {displayName}
      </span>

      {isHovered && name.length > maxLength && (
        <div className="absolute left-0 mt-1 z-10 w-max max-w-xs bg-white border border-gray-300 rounded shadow-lg p-2 text-gray-900 text-sm">
          {name}
        </div>
      )}
    </div>
  );
};

export default EmployeeNameCell;
