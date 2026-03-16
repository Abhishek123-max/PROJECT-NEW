"use client";
import React, { useState, useEffect } from "react";
import Popup from "@/components/ui/Popup";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Dropdown from "@/components/ui/dropdown";
import SuccessPopup from "@/components/popup/SuccessPopup";

const CreateTableForm = ({ isOpen, onClose, onAdd, table }) => {
  const [tableNo, setTableNo] = useState("");
  const [noOfSeats, setNoOfSeats] = useState("");
  const [status, setStatus] = useState("");
  const [floor, setFloor] = useState("");
  const [hall, setHall] = useState("");
  const [assigned, setAssigned] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);

  const isEdit = !!table;

  useEffect(() => {
    if (table) {
      setTableNo(table.tableNo || "");
      setNoOfSeats(table.noOfSeats || "");
      setStatus(table.status || "");
      setFloor(table.floor || "");
      setHall(table.hall || "");
      setAssigned(table.assigned || "");
    }
  }, [table]);

  const handleSubmit = (e) => {
    e.preventDefault();

    const tableData = {
      tableNo,
      noOfSeats,
      status,
      floor,
      hall,
      assigned,
    };

    console.log("✅ Table Data Submitted:", tableData);

    if (onAdd) onAdd(tableData);
    setShowSuccess(true);
  };

  if (!isOpen) return null;

  return (
    <>
      <Popup onClose={onClose} className="w-[516px]">
        <form onSubmit={handleSubmit} className="my-6 py-3 px-2">
          {/* Title */}
          <div className="text-center mb-6 flex flex-col gap-2">
            <h2 className="text-[26px] font-[700]">
              {isEdit ? "Edit Table" : "Add Table"}
            </h2>
            <p className="text-[14px] text-[#adabbb] leading-[24px]">
              {isEdit
                ? ""
                : "Enter table details including seats, hall, and assignment"}
            </p>
          </div>

          {/* Table Number (Full Width) */}
          <Input
            label="Table Number"
            placeholder="e.g. T12"
            value={tableNo}
            onChange={(e) => setTableNo(e.target.value)}
            required
            className="!placeholder:text-[14px] w-full"
          />

          {/* Dropdown Row — No of Seats & Status */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            {/* No of Seats */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                No. of Seats<span className="text-red-500">*</span>
              </label>
              <Dropdown
                name="noOfSeats"
                value={noOfSeats}
                onChange={(e) => setNoOfSeats(e.target.value)}
                options={[
                  { value: "2", label: "2" },
                  { value: "4", label: "4" },
                  { value: "6", label: "6" },
                  { value: "8", label: "8" },
                ]}
                placeholder="Select Seats"
                theme={{
                  surface: "#FFFFFF",
                  text: "#131313",
                  border: "#ECECEC",
                }}
                className="h-12 !py-3 !border-none !shadow-none text-[14px]"
              />
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Status<span className="text-red-500">*</span>
              </label>
              <Dropdown
                name="status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                options={[
                  { value: "available", label: "Available" },
                  { value: "occupied", label: "Occupied" },
                  { value: "reserved", label: "Reserved" },
                  { value: "maintenance", label: "Maintenance" },
                ]}
                placeholder="Select Status"
                theme={{
                  surface: "#FFFFFF",
                  text: "#131313",
                  border: "#ECECEC",
                }}
                className="h-12 !py-3 !border-none !shadow-none text-[14px]"
              />
            </div>
          </div>

          {/* Dropdown Row — Floor & Hall (same line) */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            {/* Floor */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Floor<span className="text-red-500">*</span>
              </label>
              <Dropdown
                name="floor"
                value={floor}
                onChange={(e) => setFloor(e.target.value)}
                options={[
                  { value: "1", label: "1" },
                  { value: "2", label: "2" },
                  { value: "3", label: "3" },
                  { value: "4", label: "4" },
                ]}
                placeholder="Select Floor"
                theme={{
                  surface: "#FFFFFF",
                  text: "#131313",
                  border: "#ECECEC",
                }}
                className="h-12 !py-3 !border-none !shadow-none text-[14px]"
              />
            </div>

            {/* Hall */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Hall<span className="text-red-500">*</span>
              </label>
              <Dropdown
                name="hall"
                value={hall}
                onChange={(e) => setHall(e.target.value)}
                options={[
                  { value: "ac-dining", label: "AC Dining" },
                  { value: "non-ac-dining", label: "Non-AC Dining" },
                  { value: "family-hall", label: "Family Hall" },
                  { value: "couples-hall", label: "Couples Hall" },
                ]}
                placeholder="Select Hall"
                theme={{
                  surface: "#FFFFFF",
                  text: "#131313",
                  border: "#ECECEC",
                }}
                className="h-12 !py-3 !border-none !shadow-none text-[14px]"
              />
            </div>
          </div>

          {/* Assigned (Full Width) */}
          <div className="w-full">
          <Input
            label="Assigned To"
            placeholder="e.g. John (Waiter)"
            value={assigned}
            onChange={(e) => setAssigned(e.target.value)}
            required
            className="!placeholder:text-[14px] w-full mt-4 !mb-2 "
          />
           {assigned && (
                <div className="inline-flex items-center space-x-2 border border-gray-300 rounded-lg px-3 py-1 bg-gray-100">
                  <span className="flex items-center justify-center w-[26px] h-[26px] rounded-full bg-purple-600 text-white font-semibold text-[14px]">
                    {assigned.substring(0, 2).toUpperCase()}
                  </span>
                  <span className="text-gray-700 text-[14px]">{assigned}</span>
                </div>
              )}
</div>
          {/* Action Buttons */}
          <div className="flex justify-center gap-[10px] mt-6">
            <Button
              size="large"
              variant="text"
              type="button"
              className="w-full"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              size="large"
            >
              {isEdit ? "Save Changes" : "Add Table"}
            </Button>
          </div>
        </form>
      </Popup>

    
    </>
  );
};

export default CreateTableForm;
