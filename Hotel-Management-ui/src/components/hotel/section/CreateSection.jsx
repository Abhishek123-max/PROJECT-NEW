"use client";
import React, { useState, useEffect } from "react";
import Popup from "@/components/ui/Popup";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Dropdown from "@/components/ui/dropdown";
import SuccessPopup from "@/components/popup/SuccessPopup";

const CreateSection = ({ isOpen, onClose, onAdd, section }) => {
  const [sectionName, setSectionName] = useState("");
  const [sectionType, setSectionType] = useState("");
  const [tables, setTables] = useState([]);
  const [showSuccess, setShowSuccess] = useState(false);

  const isEdit = !!section;

  useEffect(() => {
    if (section) {
      setSectionName(section.sectionName || "");
      setSectionType(section.sectionType || "");
      setTables(section.tables || []);
    }
  }, [section]);

  const tableOptions = [
    { value: "T1", label: "Table 1" },
    { value: "T2", label: "Table 2" },
    { value: "T3", label: "Table 3" },
    { value: "T4", label: "Table 4" },
    { value: "T5", label: "Table 5" },
  ];

  // Handle adding table
  const handleTableSelect = (e) => {
    const selectedValue = e.target.value;
    const tableObj = tableOptions.find((t) => t.value === selectedValue);
    if (tableObj && !tables.some((t) => t.value === selectedValue)) {
      setTables((prev) => [...prev, tableObj]);
    }
  };

  // Handle removing table
  const handleRemoveTable = (value) => {
    setTables((prev) => prev.filter((t) => t.value !== value));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const sectionData = { sectionName, sectionType, tables };
    console.log("✅ Section Data Submitted:", sectionData);
    if (onAdd) onAdd(sectionData);
    setShowSuccess(true);
  };

  if (!isOpen) return null;

  return (
    <>
      <Popup onClose={onClose} className="w-[516px]">
        <form onSubmit={handleSubmit} className="my-6 py-3 px-4">
          {/* Title */}
          <div className="text-center mb-6 flex flex-col gap-2">
            <h2 className="text-[26px] font-[700]">
              {isEdit ? "Edit Section" : "Add Section"}
            </h2>
            <p className="text-[14px] text-[#adabbb] leading-[24px]">
              {isEdit ? "" : "Provide section details and assign tables below."}
            </p>
          </div>

          {/* Section Fields */}
          <div className="grid grid-cols-1 mb-4">
            <Input
              label="Section Name"
              placeholder="e.g. West Wing"
              value={sectionName}
              onChange={(e) => setSectionName(e.target.value)}
              required
              className="!placeholder:text-[14px]"
            />

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Section Type<span className="text-red-500">*</span>
              </label>
              <Dropdown
                name="sectionType"
                value={sectionType}
                onChange={(e) => setSectionType(e.target.value)}
                options={[
                  { value: "dining", label: "Dining" },
                  { value: "vip", label: "VIP" },
                  { value: "outdoor", label: "Outdoor" },
                  { value: "private", label: "Private" },
                ]}
                placeholder="Select Section Type"
                theme={{
                  surface: "#fff",
                  text: "#000",
                  border: "#ccc",
                }}
                className="h-12 !py-3 !border-none !shadow-none text-[14px]"
              />
            </div>
          </div>

        
          {/* Multi-select Table Dropdown */}
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Tables <span className="text-red-500">*</span>
            </label>
            <Dropdown
              placeholder="Select Tables"
              options={tableOptions.filter(
                (option) =>
                  !tables.some((table) => table.value === option.value)
              )} // Filter out already selected tables
              onChange={handleTableSelect} // use onChange instead of onSelect
              value="" // no single value for multi-select
              theme={{
                surface: "#fff",
                text: "#000",
                border: "#ccc",
              }}
            />
            <div className="flex flex-wrap gap-2 mt-2">
              {tables.map((table) => (
                <span
                  key={table.value}
                  className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full"
                >
                  {table.label}
                  <button
                    type="button"
                    className="ml-2 text-green-800 hover:text-green-900 focus:outline-none"
                    onClick={() => handleRemoveTable(table.value)}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
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
              {isEdit ? "Save Changes" : "Add Section"}
            </Button>
          </div>
        </form>
      </Popup>

     
    </>
  );
};

export default CreateSection;
