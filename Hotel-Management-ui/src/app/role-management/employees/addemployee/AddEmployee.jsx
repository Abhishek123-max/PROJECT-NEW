"use client";
import React, { useState } from "react";
import Popup from "@/components/ui/Popup";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Dropdown from "@/components/ui/dropdown";
import PhoneInput from "react-phone-input-2";
import "react-phone-input-2/lib/style.css";
import SuccessPopup from "@/components/popup/SuccessPopup";

const AddEmployee = ({ isOpen, onClose, onAdd, employee }) => {
  const [employeeName, setEmployeeName] = useState(employee?.employeeName || "");
  const [employeeId, setEmployeeId] = useState(employee?.employeeId || "");
  const [emailAddress, setEmailAddress] = useState(employee?.emailAddress || "");
  const [phoneNumber, setPhoneNumber] = useState(employee?.phoneNumber || "");
  const [role, setRole] = useState(employee?.role || "");
  const [reportingManager, setReportingManager] = useState(employee?.reportingManager || "");
  const [password, setPassword] = useState(employee?.password || generatePassword());

  const [showSuccess, setShowSuccess] = useState(false); 

  function generatePassword() {
    return (
      Math.random().toString(36).substring(2, 10) +
      Math.random().toString(36).substring(2, 8)
    );
  }

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

    const employeeData = {
      employeeName,
      employeeId,
      emailAddress,
      phoneNumber,
      role,
      reportingManager,
      password,
    };

    console.log("Employee Data Submitted:", employeeData);

    if (onAdd) onAdd(employeeData);

    // Show SuccessPopup
    setShowSuccess(true);
  };

  const handleCopyPassword = () => {
    navigator.clipboard.writeText(password);
    alert("Password copied to clipboard!");
  };

  const handleRefreshPassword = () => {
    const newPassword =
      Math.random().toString(36).substring(2, 10) +
      Math.random().toString(36).substring(2, 8);
    setPassword(newPassword);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Add/Edit Employee Form */}
      <Popup onClose={onClose} className="w-[636px]">
        <form onSubmit={handleSubmit} className="my-6 py-3 px-2">
          {/* Title */}
          <div className=" text-center mb-6 flex flex-col gap-2">
            <h2 className="text-[26px] font-[700]">
              {isEdit ? "Edit Employee" : "Add Employee"}
            </h2>
            <p className="text-[14px] text-[#adabbb] leading-[24px]">
              {isEdit ? "" : "Add employee profile to start assigning roles, permissions, and managing operations."}
            </p>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-[20px]">
            <Input
              label="Employee Name"
              placeholder="eg. Amruth Srivastava"
              value={employeeName}
              onChange={(e) => setEmployeeName(e.target.value)}
              required
              className="!placeholder:text-[14px]"
            />

            <Input
              label="Employee ID"
              placeholder="eg. EMPL0001"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              required
              className="placeholder:text-[14px]"
            />

            <Input
              label="Email Address"
              type="email"
              placeholder="eg. harish3243@gmail.com"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              required
              className="!placeholder:text-[14px]"
            />

            {/* Phone Number */}
            <div className="flex gap-1 flex-col">
              <label className="block text-sm font-semibold text-gray-700">
                Phone Number <span className="text-red-500">*</span>
              </label>

              <PhoneInput
                country="in"
                value={phoneNumber}
                onChange={(phone, data) => {
                  const countryCode = `+${data.dialCode}`;
                  if (!phone.startsWith(countryCode)) {
                    phone = countryCode + phone.replace(/^\+?[0-9]*/, "");
                  }
                  setPhoneNumber(phone);
                }}
                inputStyle={{
                  width: "287.5px",
                  height: "46px",
                  borderRadius: "10px",
                  border: "2px solid #E6E6E6",
                  background: "#FFFFFF",
                  paddingLeft: "48px",
                }}
                buttonStyle={{
                  borderRadius: "10px 0 0 10px",
                  border: "1px solid #E6E6E6",
                  background: "#FFFFFF",
                  height: "46px",
                  width: "48px",
                }}
                enableSearch={false}
                required
              />
            </div>

            {/* Role */}
            <div className="mb-[20px]">
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Role <span className="text-red-500">*</span>
              </label>
              <Dropdown
                name="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                options={[
                  { value: "cashier", label: "Cashier" },
                  { value: "manager", label: "Manager" },
                  { value: "admin", label: "Admin" },
                  { value: "supervisor", label: "Supervisor" },
                ]}
                placeholder="Select Role"
                theme={{
                  surface: "#FFFFFF",
                  text: "#131313",
                  border: "#ECECEC",
                }}
                className="h-12 !py-3 !border-none !shadow-none text-[14px]"
              />
              {role && (
                <div className="inline-flex items-center space-x-2 border border-gray-300 rounded-lg px-3 py-1 mt-4 bg-gray-100">
                  <span className="text-gray-700 text-[14px]">{role}</span>
                </div>
              )}
            </div>

            {/* Reporting Manager */}
            <div className="w-full">
              <Input
                label="Reporting Manager"
                placeholder="Sujil"
                value={reportingManager}
                onChange={(e) => setReportingManager(e.target.value)}
                required
                className="placeholder:text-sm w-full !mb-2"
              />

              {reportingManager && (
                <div className="inline-flex items-center space-x-2 border border-gray-300 rounded-lg px-3 py-1 bg-gray-100">
                  <span className="flex items-center justify-center w-[26px] h-[26px] rounded-full bg-purple-600 text-white font-semibold text-[14px]">
                    {reportingManager.substring(0, 2).toUpperCase()}
                  </span>
                  <span className="text-gray-700 text-[14px]">{reportingManager}</span>
                </div>
              )}
            </div>

            {/* Password */}
            <div className="col-span-1 md:col-span-2">
              <Input
                label="Password"
                type="text"
                value={password}
                readOnly
                showPasswordToggle
                className="placeholder:text-[14px]"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center gap-[10px] mt-3">
            <Button
              size="large"
              variant="text"
              type="button"
              className="w-full"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" className="w-full" size="large"  onClick={handleSubmit}>
              {isEdit ? "Save Changes" : "Add"}
            </Button>
          </div>
        </form>
      </Popup>

   
    </>
  );
};

export default AddEmployee;
