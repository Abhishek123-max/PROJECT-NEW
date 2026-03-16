"use client";
import React from "react";
import EmptyState from "@/components/emptyState/EmptyState";

const FloorLists = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-semibold text-gray-900">
              Ground Floor
            </span>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 text-gray-500 cursor-pointer"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              Halls: <span className="font-medium">7</span>
            </div>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              Floor: 1
            </span>
            <button className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 rounded-full">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"
                />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-center">
        <div className="bg-gray-100 rounded-full w-48 h-48 flex items-center justify-center overflow-hidden mb-6">
          {/* Placeholder for the building illustration */}
          {/* You would replace this with an actual SVG or image component */}
          <div className="relative w-full h-full">
            {/* Simple building illustration - replace with actual SVG */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-green-700 rounded-lg shadow-md">
              <div className="absolute inset-0 p-2 flex flex-wrap gap-1">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-5 h-5 bg-green-500 rounded-sm"
                  ></div>
                ))}
              </div>
            </div>
            <div className="absolute right-8 bottom-8 w-12 h-24 bg-green-600 rounded-t-full rotate-12 origin-bottom-right"></div>
            <div className="absolute right-12 bottom-0 w-8 h-16 bg-green-500 rounded-t-full -rotate-12 origin-bottom-left"></div>
            <div className="absolute right-4 bottom-4 w-4 h-8 bg-green-400 rounded-t-full rotate-45 origin-bottom-right"></div>
          </div>
        </div>

      
     

        
      </main>
    </div>
  );
};

export default FloorLists;
