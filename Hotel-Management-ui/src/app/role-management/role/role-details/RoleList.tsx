"use client";

import React, { useState, useMemo, useEffect } from "react";
import Table from "@/components/table/Table";
import Button from "@/components/ui/Button";
import SearchInput from "@/components/ui/SearchInput";
import ActionDropdown from "@/components/actiondropdown/ActionDropdown";
import Drawer from "@/components/ui/Drawer";
import RoleDetails from "@/components/role/RoleDetails";
import Pagination from "@/components/pagination/Pagination";
import { roleService } from "@/api/roles";
import { Role } from "@/types/roles";

interface RoleListProps {
  onCreateRole: () => void;
}

const RoleList: React.FC<RoleListProps> = ({ onCreateRole }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRows, setSelectedRows] = useState<number[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const rowsPerPage = 10;

  // ✅ Fetch roles from API
  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const response = await roleService.getAllRoles();
        if (response.roles && Array.isArray(response.roles)) {
          setRoles(response.roles);
        } else {
          console.error("Unexpected roles format:", response);
        }
      } catch (error) {
        console.error("Failed to fetch roles:", error);
      }
    };

    fetchRoles();
  }, []);

  // Handlers
  const handleDelete = (roleToDelete: Role) => {
    setRoles((prev) => prev.filter((role) => role.id !== roleToDelete.id));
  };

  const handleEdit = (role: Role) => {
    console.log("Editing role:", role);
  };

  const handleViewDetails = (role: Role) => {
    setSelectedRole(role);
    setIsDrawerOpen(true);
  };

  const toggleRow = (id: number) => {
    setSelectedRows((prev) =>
      prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    if (selectedRows.length === roles.length) {
      setSelectedRows([]);
    } else {
      setSelectedRows(roles.map((role) => role.id));
    }
  };

  // ✅ Filter roles
  const filteredRoles = useMemo(
    () =>
      roles.filter(
        (role) =>
          role.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          role.description.toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [roles, searchTerm]
  );

  // ✅ Pagination
  const totalPages = Math.ceil(filteredRoles.length / rowsPerPage);
  const paginatedRoles = filteredRoles.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  // ✅ Table Columns (Design Unchanged)
  const columns = [
    {
      header: (
        <input
          type="checkbox"
          className="w-5 h-5 text-blue-600 rounded"
          style={{ cursor: "pointer", border: "1px solid #D1D1D6" }}
          checked={selectedRows.length === roles.length && roles.length > 0}
          onChange={toggleAll}
        />
      ),
      accessor: "select",
      width: "20px",
      render: (role: Role) => (
        <input
          type="checkbox"
          className="w-5 h-5 text-blue-600 rounded"
          style={{ cursor: "pointer", border: "1px solid #D1D1D6" }}
          checked={selectedRows.includes(role.id)}
          onChange={() => toggleRow(role.id)}
        />
      ),
    },
    {
      header: "Role",
      accessor: "display_name",
      width: "176px",
      render: (role: Role) => (
        <span className="font-medium text-gray-800">{role.display_name}</span>
      ),
    },
    {
      header: "Staff Assigned",
      accessor: "staff",
      width: "553px",
      render: () => (
        <span className="text-gray-500">—</span> // Placeholder until staff assignment is implemented
      ),
    },
    {
      header: "Permissions",
      accessor: "permissions",
      width: "150px",
      render: (role: Role) => (
        <span className="font-medium text-gray-800 ml-3">
          {Object.keys(role.permissions || {}).length}
        </span>
      ),
    },
    {
      header: "Action",
      accessor: "action",
      width: "137px",
      render: (role: Role) => (
        <div className="relative overflow-visible">
          <ActionDropdown
            row={role}
            onViewDetails={() => handleViewDetails(role)}
            onEdit={() => handleEdit(role)}
            onDelete={() => handleDelete(role)}
          />
        </div>
      ),
    },
  ];

  return (
    <div className="p-6 h-[890px] rounded-lg">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-[22px] font-[700] text-[#17181A]">Role Management</h2>
        <div className="flex items-center space-x-4">
          <SearchInput
            value={searchTerm}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
            placeholder="Search Role"
          />

          <Button
            variant="primary"
            size="large"
            className="w-[165px] h-[42px] whitespace-nowrap"
            onClick={onCreateRole}
          >
            Create Role
          </Button>
        </div>
      </div>

      <Table columns={columns} data={paginatedRoles} />

      {totalPages > 1 && (
        <div className="p-4 flex justify-end">
          <Pagination
            totalPages={totalPages}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
        </div>
      )}

      {/* Drawer */}
      <Drawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title={"Details"}
      >
        {selectedRole && <RoleDetails role={selectedRole} />}
      </Drawer>
    </div>
  );
};

export default RoleList;
