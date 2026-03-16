"use client";

import React from "react";
import { SearchIcon } from "@/assests/icons";

const SearchBar = ({ value, onChange, placeholder = "Search" }) => {
  return (
    <div className="w-full max-w-md">
      <div className="relative">
        {/* Icon inside input */}
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
          <SearchIcon width={18} height={18} />
        </span>

        {/* Input */}
        <input
          type="text"
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="w-full h-[42px] pl-10 pr-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm text-gray-700 
          placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-gray-400"
        />
      </div>
    </div>
  );
};

export default SearchBar;
