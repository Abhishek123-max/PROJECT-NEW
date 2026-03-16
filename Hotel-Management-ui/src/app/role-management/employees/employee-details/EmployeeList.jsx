"use client";

import React, { useState, useMemo } from "react";
import SearchInput from "@/components/ui/SearchInput";
import Button from "@/components/ui/Button";
import Table from "@/components/table/Table";
import Drawer from "@/components/ui/Drawer";
import ActionDropdown from "@/components/actiondropdown/ActionDropdown";
import Pagination from "@/components/pagination/Pagination";
import AddEmployee from "@/app/role-management/employees/addemployee/AddEmployee";
import EmployeeNameCell from "@/components/role/EmployeeNameCell";
import SuccessPopup from "@/components/popup/SuccessPopup";

// Dummy employee data
const dummyEmployees = [
  {
    id: "EMPL00001",
    name: "Sharath Kumar patil patil",
    contact: { phone: "+91 7349318984", email: "sharath1111@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "13 May 2025",
  },
  {
    id: "EMPL00002",
    name: "Vikram Saini",
    contact: { phone: "+91 7349318984", email: "sharath1111@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "13 May 2025",
  },
  {
    id: "EMPL00003",
    name: "Siddharth",
    contact: { phone: "+91 7349318984", email: "sharath1111@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "13 May 2025",
  },
  {
    id: "EMPL00004",
    name: "Aditya Verma",
    contact: { phone: "+91 7349318984", email: "sharath1111@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "13 May 2025",
  },
  {
    id: "EMPL00005",
    name: "Devansh",
    contact: { phone: "+91 7349318984", email: "sharath1111@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "13 May 2025",
  },
  {
    id: "EMPL00006",
    name: "Samaya Rana",
    contact: { phone: "+91 7349318984", email: "sharath1111@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "13 May 2025",
  },
  {
    id: "EMPL00007",
    name: "Sharath Kumar",
    contact: { phone: "+91 7349318984", email: "sharath1111@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "13 May 2025",
  },
  {
    id: "EMPL00008",
    name: "Employee 8",
    contact: { phone: "+91 1234567890", email: "emp8@gmail.com" },
    role: "Manager",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "14 May 2025",
  },
  {
    id: "EMPL00009",
    name: "Employee 9",
    contact: { phone: "+91 1234567890", email: "emp9@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "14 May 2025",
  },
  {
    id: "EMPL00010",
    name: "Employee 10",
    contact: { phone: "+91 1234567890", email: "emp10@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "14 May 2025",
  },
  {
    id: "EMPL00011",
    name: "Employee 11",
    contact: { phone: "+91 1234567890", email: "emp11@gmail.com" },
    role: "Cashier",
    manager: { name: "Sujith", initials: "SJ" },
    addedOn: "14 May 2025",
  },
];

const EmployeeList = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [employees, setEmployees] = useState(dummyEmployees);
  const [selectedRows, setSelectedRows] = useState([]);
  const [showAddPopup, setShowAddPopup] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [editEmployee, setEditEmployee] = useState(null);
  const rowsPerPage = 10;

  // Handle edit click
  const handleEditClick = (employee) => {
    setEditEmployee(employee);
    setShowAddPopup(true);
  };

  // Add, Edit, Delete handlers
  const handleDelete = (employee) =>
    setEmployees((prev) => prev.filter((e) => e.id !== employee.id));

  const handleAddEmployeeSubmit = (newEmployee) => {
    if (editEmployee) {
      setEmployees((prev) =>
        prev.map((e) => (e.id === editEmployee.id ? newEmployee : e))
      );
    } else {
      setEmployees((prev) => [...prev, newEmployee]);
    }

    // Close AddEmployee popup
    setShowAddPopup(false);
    setEditEmployee(null);

    // Show success popup
    setShowSuccess(true);
  };

  // Row selection
  const toggleRow = (id) =>
    setSelectedRows((prev) =>
      prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]
    );

  const toggleAll = () =>
    setSelectedRows((prev) =>
      prev.length === employees.length ? [] : employees.map((e) => e.id)
    );

  // Filtered and paginated employees
  const filteredEmployees = useMemo(() => {
    return employees.filter((employee) => {
      const name = employee?.name || "";
      const email = employee?.contact?.email || "";
      const role = employee?.role || "";
      const search = searchTerm?.toLowerCase() || "";

      return (
        name.toLowerCase().includes(search) ||
        email.toLowerCase().includes(search) ||
        role.toLowerCase().includes(search)
      );
    });
  }, [employees, searchTerm]);

  const totalPages = Math.ceil(filteredEmployees.length / rowsPerPage);
  const paginatedEmployees = filteredEmployees.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  // Table columns
  const columns = [
    {
      header: (
        <input
          type="checkbox"
          className="w-5 h-5 text-blue-600 rounded"
          checked={
            selectedRows.length === employees.length && employees.length > 0
          }
          onChange={toggleAll}
        />
      ),
      accessor: "select",
      width: "20px",
      render: (row) => (
        <input
          type="checkbox"
          className="w-5 h-5 text-blue-600 rounded"
          checked={selectedRows.includes(row.id)}
          onChange={() => toggleRow(row.id)}
        />
      ),
    },
    {
      header: "Employee ID",
      accessor: "id",
      render: (row) => <span className="font-medium text-gray-800">{row.id}</span>,
    },
    {
      header: "Employee Name",
      accessor: "name",
      render: (row) => <EmployeeNameCell name={row.name} />,
    },
    {
      header: "Contact Details",
      accessor: "contact",
      render: (row) => (
        <div className="text-gray-700">
          <p>{row.contact?.phone || "N/A"}</p>
          <p>{row.contact?.email || "N/A"}</p>
        </div>
      ),
    },
    {
      header: "Role",
      accessor: "role",
      render: (row) => <span className="font-medium text-gray-800">{row.role}</span>,
    },
    {
      header: "Reporting Manager",
      accessor: "manager",
      render: (row) => (
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center text-sm font-bold">
            {row.manager?.initials || "NA"}
          </div>
          <span className="text-gray-800">{row.manager?.name || "N/A"}</span>
        </div>
      ),
    },
    {
      header: "Added On",
      accessor: "addedOn",
      render: (row) => <span className="font-medium text-gray-800">{row.addedOn}</span>,
    },
    {
      header: "Action",
      accessor: "action",
      width: "137px",
      render: (row) => (
        <div className="relative overflow-visible">
          <ActionDropdown
            row={row}
            onEdit={() => {
              if (selectedRows.length !== 1) {
                alert("Select only one row to edit");
                return;
              }
              handleEditClick(row);
            }}
            onDelete={() => {
              if (selectedRows.length !== 1) {
                alert("Select only one row");
                return;
              }
              handleDelete(row);
            }}
          />
        </div>
      ),
    },
  ];

  return (
    <div className="p-6 h-[890px] flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-[22px] font-[700] text-[#17181A]">Employee Management</h2>
        <div className="flex items-center space-x-4">
          <SearchInput
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search Employee"
            className="!w-[250px]"
          />
          <Button
            variant="primary"
            size="large"
            className="w-[165px] h-[42px] whitespace-nowrap"
            onClick={() => setShowAddPopup(true)}
          >
            Add Employee
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <Table columns={columns} data={paginatedEmployees} />
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-4 flex justify-end items-end">
          <Pagination
            totalPages={totalPages}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
        </div>
      )}

      {/* Drawer */}
      <Drawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} />

      {/* Add/Edit Employee */}
      <AddEmployee
        isOpen={showAddPopup}
        onClose={() => {
          setShowAddPopup(false);
          setEditEmployee(null);
        }}
        employee={editEmployee}
        onAdd={handleAddEmployeeSubmit}
      />

      {/* Success Popup */}
      {showSuccess && (
        <SuccessPopup
          title="Employee Added Successfully"
          subtitle="The employee profile has been created and ready to assign roles and permissions."
          onClose={() => setShowSuccess(false)}
          onConfirm={() => setShowSuccess(false)}
        />
      )}
    </div>
  );
};

export default EmployeeList;


