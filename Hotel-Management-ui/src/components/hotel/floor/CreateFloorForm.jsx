"use client";
import React, { useState } from "react";
import Popup from "@/components/ui/Popup";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Dropdown from "@/components/ui/dropdown";
import PhoneInput from "react-phone-input-2";
import "react-phone-input-2/lib/style.css";
import SuccessPopup from "@/components/popup/SuccessPopup";
import SearchBar from "@/components/ui/SearchInput";

const CreateFloorForm = ({ isOpen, onClose, onAdd, employee }) => {
  const [floorName, setFloorName] = useState("");

  const [floorNumber, setFloorNumber] = useState("");
  const [FloorManager, setFloorManager] = useState("");

  const [showSuccess, setShowSuccess] = useState(false);

  const isEdit = !!employee;

  React.useEffect(() => {
    if (employee) {
      setEmployeeName(employee.employeeName || "");
      setEmployeeId(employee.employeeId || "");
      setEmailAddress(employee.emailAddress || "");
      setPhoneNumber(employee.phoneNumber || "");
      setRole(employee.role || "");
      setReportingManager(employee.reportingManager || "");
      setPassword(employee.password || generatePassword());
    }
  }, [employee]);

  const handleSubmit = (e) => {
    e.preventDefault();

    const floorData = {
      floorName,
      floorNumber,
      FloorManager,
    };

    console.log("FloorData Submitted:", floorData);

    if (onAdd) onAdd(floorData);

    // Show SuccessPopup
    setShowSuccess(true);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Add/Edit floor Form */}
      <Popup onClose={onClose} className="w-[516px]">
        <form onSubmit={handleSubmit} className="my-6 py-3 px-2">
          {/* Title */}
          <div className=" text-center mb-6 flex flex-col gap-2">
            <h2 className="text-[26px] font-[700]">
              {isEdit ? "Edit Floor" : "Add Floor"}
            </h2>
            <p className="text-[14px] text-[#adabbb] leading-[24px]">
              {isEdit ? "" : "Give it a name and select floors"}
            </p>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-1 gap-x-[20px]">
            <Input
              label="Floor Name"
              placeholder="eg. Ground Floor"
              value={floorName}
              onChange={(e) => setFloorName(e.target.value)}
              required
              className="!placeholder:text-[14px]"
            />

            <div className="mb-[20px]">
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Floor Number<span className="text-red-500">*</span>
              </label>
              <Dropdown
                name="floorNumber"
                value={floorNumber}
                onChange={(e) => setFloorNumber(e.target.value)}
                options={[
                  { value: "1", label: "1" },
                  { value: "2", label: "2" },
                  { value: "3", label: "3" },
                  { value: "4", label: "4" },
                ]}
                placeholder="Select Floor Number"
                theme={{
                  surface: "#FFFFFF",
                  text: "#131313",
                  border: "#ECECEC",
                }}
                className="h-12 !py-3 !border-none !shadow-none text-[14px]"
              />
            </div>

            {/* Reporting Manager */}
            <div className="w-full ">
              <Input
                label=" Floor Manager"
                placeholder="Sujil"
                value={FloorManager}
                onChange={(e) => setFloorManager(e.target.value)}
                required
                className="placeholder:text-sm w-full !mb-2"
              />
              <div className="mt-0">
                {FloorManager && (
                  <div className="inline-flex items-center space-x-2 border border-gray-300 rounded-lg px-3 py-1 bg-gray-100 ">
                    <span className="flex items-center justify-center w-[26px] h-[26px] rounded-full bg-purple-600 text-white font-semibold text-[14px]">
                      {FloorManager.substring(0, 2).toUpperCase()}
                    </span>
                    <span className="text-gray-700 text-[14px]">
                      {FloorManager}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center gap-[10px] mt-4">
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
              onClick={handleSubmit}
            >
              {isEdit ? "Save Changes" : "Add Floor"}
            </Button>
          </div>
        </form>
      </Popup>
    </>
  );
};

export default CreateFloorForm;
