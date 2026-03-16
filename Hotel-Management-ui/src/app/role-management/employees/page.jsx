"use client";
import React from "react";
import role from "@/assests/role.png";

import EmptyState from "@/components/emptyState/EmptyState";
import { useRouter } from "next/navigation";
import useNavigation from "@/hooks/useNavigation";
import EmployeeList from '@/app/role-management/employees/employee-details/EmployeeList'

const Employee = () => {
  const router = useRouter();
  const { handleCreateRole, handleBack } = useNavigation();

  return (
    <div>
      {/* <EmptyState
        iconSrc={role}
        iconAlt="No Employees Added Yet"
        title="No Roles Added Yet"
        description={
          <>
            You haven’t added any employees. Add employee profile to start{" "}
            <br /> assigning roles, permissions, and managing operations.
          </>
        }
        backButtonText="Back"
        createButtonText="Add Employee"
        onCreateClick={handleCreateRole}
        onBackClick={handleBack}
      /> */}
      <EmployeeList/>
    </div>
  );
};

export default Employee;
