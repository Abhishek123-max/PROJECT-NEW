"use client";
import { useState } from "react";
import { UpArrow, RightArrow } from "@/assests/icons";

const HotelDetails = () => {
  const [openSections, setOpenSections] = useState({
    summary: true,
    address: false,
  });

  const toggleSection = (section) => {
    setOpenSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const summaryData = [
    { label: "Name", value: "Hotel Empire" },
    { label: "Business Type", value: "Restaurant" },
    { label: "Website", value: "hotelempire.in" },
    { label: "GST Number", value: "433AAAAAAAAAA0000987" },
    { label: "FSSAI License No.", value: "74626353487257732762" },
  ];

  const addressData = [
    { label: "Address Line 1", value: "Empire Hotel, No. 45" },
    { label: "Address Line 2", value: "Koramangala 8th Block" },
    { label: "Area", value: "Koramangala" },
    { label: "City", value: "Bangalore" },
    { label: "Pin code", value: "560068" },
  ];

  return (
    <div className="w-full bg-gray-50 rounded-md px-1">
      {/* Summary Section */}
      <div className="border-b-[1px] border-[#ececec] py-4">
        <div className="flex justify-between items-center w-full py-4 text-left font-[700] text-[#0e0e0e] text-[15px]">
          <span>Summary</span>
          <button onClick={() => toggleSection("summary")} className="cursor-pointer">
            {openSections.summary ? <UpArrow /> : <RightArrow />}
          </button>
        </div>

        {openSections.summary && (
          <div className=" text-[14px] flex flex-col gap-[18px]">
            {summaryData.map((item, index) => (
              <div key={index} className="flex justify-between">
                <span className="text-[#adabbb]">{item.label}</span>
                <span className="font-medium text-[#0e0e0e]">{item.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Address Section */}
      <div className="border-b-[1px] border-[#ececec] py-4">
        <div className="flex justify-between items-center w-full py-4 text-left font-[700] text-[#0e0e0e] text-[15px]">
          <span>Address</span>
          <button onClick={() => toggleSection("address")} className="cursor-pointer">
            {openSections.address ? <UpArrow /> : <RightArrow />}
          </button>
        </div>

        {openSections.address && (
          <div className=" text-[14px] flex flex-col gap-[18px]">
            {addressData.map((item, index) => (
              <div key={index} className="flex justify-between">
                <span className="text-[#adabbb]">{item.label}</span>
                <span className="font-medium text-[#0e0e0e]">{item.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HotelDetails;
