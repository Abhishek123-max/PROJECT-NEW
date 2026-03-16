"use client";
import React from "react";

const Pagination = ({ totalPages, currentPage, onPageChange }) => {
  const displayPages = [];

  // Always show first 4 pages
  for (let i = 1; i <= Math.min(4, totalPages); i++) {
    displayPages.push(i);
  }

  // Add "..." if currentPage is beyond 5 and not near the end
  if (currentPage > 5 && totalPages > 6) {
    displayPages.push("...");
  }

  // Show the current page if it’s not in the first 4 or last page
  if (currentPage > 4 && currentPage < totalPages - 2) {
    displayPages.push(currentPage);
  }

  // Add "..." before last page if needed
  if (currentPage < totalPages - 3 && totalPages > 6) {
    displayPages.push("...");
  }

  // Always show last page
  if (totalPages > 4) {
    displayPages.push(totalPages);
  }

  return (
    <nav className="flex items-center space-x-2">
      {/* Prev button */}
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-1 text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        &lt;
      </button>

      {displayPages.map((page, index) =>
        page === "..." ? (
          <span key={index} className="px-3 py-1 text-gray-500">
            ...
          </span>
        ) : (
          <button
            key={index}
            onClick={() => onPageChange(page)}
            className={`px-3 py-1 rounded-full ${
              currentPage === page
                ? "bg-green-500 text-white"
                : "text-gray-700 hover:bg-gray-200"
            }`}
          >
            {page}
          </button>
        )
      )}

      {/* Next button */}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-1 text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        &gt;
      </button>
    </nav>
  );
};

export default Pagination;
