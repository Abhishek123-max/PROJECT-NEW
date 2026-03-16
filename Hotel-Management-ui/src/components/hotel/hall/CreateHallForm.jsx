"use client";
import React, { useState, useEffect } from "react";
import Popup from "@/components/ui/Popup";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Dropdown from "@/components/ui/dropdown";
import SuccessPopup from "@/components/popup/SuccessPopup";

const CreateHallForm = ({ isOpen, onClose, onAdd, hall }) => {
  const [hallName, setHallName] = useState("");
  const [floor, setFloor] = useState("");
  const [hallType, setHallType] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);

  const isEdit = !!hall;

  useEffect(() => {
    if (hall) {
      setHallName(hall.hallName || "");
      setFloor(hall.floor || "");
      setHallType(hall.hallType || "");
    }
  }, [hall]);

  const handleSubmit = (e) => {
    e.preventDefault();

    const hallData = { hallName, floor, hallType };

    console.log("✅ Hall Data Submitted:", hallData);

    if (onAdd) onAdd(hallData);
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
              {isEdit ? "Edit Hall" : "Add Hall"}
            </h2>
            <p className="text-[14px] text-[#adabbb] leading-[24px]">
              {isEdit
                ? ""
                : "Provide hall details including name, floor, and type"}
            </p>
          </div>

          {/* Form Fields */}
          <div className="flex flex-col ">
            {/* Hall Name */}
            <div>
              <Input
                label="Hall Name"
                placeholder="e.g. Royal Dining Hall"
                value={hallName}
                onChange={(e) => setHallName(e.target.value)}
                required
                className="!placeholder:text-[14px]"
              />
            </div>
            {/* Floor Dropdown */}
            <div className="mb-4">
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

            {/* Hall Type Dropdown */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Hall Type<span className="text-red-500">*</span>
              </label>
              <Dropdown
                name="hallType"
                value={hallType}
                onChange={(e) => setHallType(e.target.value)}
                options={[
                  { value: "ac-dining", label: "AC Dining" },
                  { value: "non-ac-dining", label: "Non-AC Dining" },
                  { value: "family-hall", label: "Family Hall" },
                  { value: "couples-hall", label: "Couples Hall" },
                ]}
                placeholder="Select Hall Type"
                theme={{
                  surface: "#FFFFFF",
                  text: "#131313",
                  border: "#ECECEC",
                }}
                className="h-12 !py-3 !border-none !shadow-none text-[14px]"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center gap-[10px] mt-8">
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
              {isEdit ? "Save Changes" : "Add Hall"}
            </Button>
          </div>
        </form>
      </Popup>

      {/* ✅ Success Popup */}
      {showSuccess && (
        <SuccessPopup
          title="Success!"
          subtitle="Hall details saved successfully."
          onClose={() => setShowSuccess(false)}
        />
      )}
    </>
  );
};

export default CreateHallForm;
