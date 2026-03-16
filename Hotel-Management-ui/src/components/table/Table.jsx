"use client";

import React from "react";

const Table = ({ columns, data }) => {
  return (
    <div className="overflow-visible border-[1px] border-[#e6e6e6] rounded-[10px] ">
      <table
        className="min-w-full bg-white border-collapse "
        style={{ borderSpacing: "33px 0" }} 
      >
        <thead className="bg-[#f5f6fa]">
          <tr>
            {columns.map((column, index) => (
              <th
                key={index}
                 style={{ width: column.width }}
                className="pl-6 py-3 text-left text-[14px] font-[600] text-[#131313] border-b border-gray-200"
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column, colIndex) => (
                <td
                  key={colIndex}
                  className="px-6 py-3 whitespace-nowrap text-[14px] font-normal text-[#131313]"
                >
                  {column.render ? column.render(row) : row[column.accessor]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
