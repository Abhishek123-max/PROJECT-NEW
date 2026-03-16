"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import SuccessPopup from "@/components/popup/SuccessPopup";
import { roleService } from "@/api/roles";
import { CreateRoleRequest } from "@/types/roles";

interface CreateRoleFormProps {
  onClose?: () => void;
}

interface PermissionSet {
  create: boolean;
  edit: boolean;
  delete: boolean;
  view: boolean;
  export: boolean;
  import: boolean;
}

const CreateRoleForm: React.FC<CreateRoleFormProps> = ({ onClose }) => {
  const [roleName, setRoleName] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [showSuccess, setShowSuccess] = useState<boolean>(false);

  const [errors, setErrors] = useState<{ roleName: string; description: string }>({
    roleName: "",
    description: "",
  });

  const [permissions, setPermissions] = useState<Record<string, PermissionSet>>({
    /* dashboard: {
      create: false,
      edit: false,
      delete: false,
      view: false,
      export: false,
      import: false,
    },
    hotelManagement: {
      create: false,
      edit: false,
      delete: false,
      view: false,
      export: false,
      import: false,
    },
    menuManagement: {
      create: false,
      edit: false,
      delete: false,
      view: false,
      export: false,
      import: false,
    },
    billingManagement: {
      create: false,
      edit: false,
      delete: false,
      view: false,
      export: false,
      import: false,
    },
    inventoryManagement: {
      create: false,
      edit: false,
      delete: false,
      view: false,
      export: false,
      import: false,
    },
    reports: {
      create: false,
      edit: false,
      delete: false,
      view: false,
      export: false,
      import: false,
    },
    orders: {
      create: false,
      edit: false,
      delete: false,
      view: false,
      export: false,
      import: false,
    }, */

    "floors": {
      "create": false,
      "view": true,
      "edit": false,
      "delete": false,
      "import": false,
      "export": false
    },
    "halls": {
      "create": false,
      "view": true,
      "edit": false,
      "delete": false,
      "import": false,
      "export": false
    },
    "sections": {
      "create": false,
      "view": false,
      "edit": false,
      "delete": false,
      "import": false,
      "export": false
    },
    "tables": {
      "create": false,
      "view": true,
      "edit": true,
      "delete": false,
      "import": false,
      "export": false
    },
    "employees/staff": {
      "create": true,
      "view": true,
      "edit": true,
      "delete": false,
      "import": true,
      "export": false
    },
    "menu and pricing": {
      "create": false,
      "view": true,
      "edit": false,
      "delete": false,
      "import": false,
      "export": false
    },
    "billing and payments": {
      "create": false,
      "view": true,
      "edit": false,
      "delete": false,
      "import": false,
      "export": false
    },
    "kitchen stations": {
      "create": true,
      "view": true,
      "edit": true,
      "delete": false,
      "import": false,
      "export": false
    }
  });

  // ✅ Toggle individual permission
  const handlePermissionChange = (category: string, permission: keyof PermissionSet) => {
    setPermissions((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [permission]: !prev[category][permission],
      },
    }));
  };

  // ✅ Select All handler
  const handleSelectAll = (category: keyof typeof permissions) => {
    const allSelected = Object.values(permissions[category]).every(Boolean);
    // Explicitly build updated PermissionSet to avoid type issues
    const updated: PermissionSet = {
      create: !allSelected,
      edit: !allSelected,
      delete: !allSelected,
      view: !allSelected,
      export: !allSelected,
      import: !allSelected,
    };
    setPermissions((prev) => ({ ...prev, [category]: updated }));
  };

  // ✅ Validate form
  const validateForm = (): boolean => {
    let valid = true;
    const newErrors = { roleName: "", description: "" };

    if (!roleName.trim()) {
      newErrors.roleName = "Role name is required.";
      valid = false;
    } else if (!/^[a-zA-Z\s]+$/.test(roleName)) {
      newErrors.roleName = "Only letters and spaces are allowed.";
      valid = false;
    }

    if (!description.trim()) {
      newErrors.description = "Description is required.";
      valid = false;
    }

    setErrors(newErrors);
    return valid;
  };

  // ✅ Handle form submit
  const handleSubmit = async (e: React.FormEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (!validateForm()) return;

    const payload: CreateRoleRequest = {
      name: roleName.toLowerCase().replace(/\s+/g, "_"),
      display_name: roleName.trim(),
      description: description.trim(),
      level: 55,
      can_create_roles: ["kitchen_staff"],
      permissions,
    };

    const response = await roleService.createRole(payload);

    if (response.success) {
      setShowSuccess(true);
    } else {
      alert(response.errors?.general || "Failed to create role");
    }
  };

  // ✅ Reset form after success
  const handlePopupClose = () => {
    setShowSuccess(false);
    setRoleName("");
    setDescription("");
    onClose?.();
  };

  return (
    <>
      <div className="flex flex-col h-full">
        {/* Sticky Top */}
        <div className="sticky top-0 z-10 bg-gray-50 pb-4 flex flex-col gap-[10px]">
          <Input
            label="Role Name"
            type="text"
            placeholder="e.g. Manager"
            value={roleName}
            error={errors.roleName}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              setRoleName(e.target.value);
              if (errors.roleName) setErrors((prev) => ({ ...prev, roleName: "" }));
            }}
            required
            width="100%"
            height="48px"
          />

          <Input
            label="Description"
            placeholder="Briefly describe this role"
            value={description}
            error={errors.description}
            onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
              setDescription(e.target.value);
              if (errors.description)
                setErrors((prev) => ({ ...prev, description: "" }));
            }}
            required
            width="100%"
            height="120px"
            className="resize-none overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent"
            multiline
            rows={4}
          />
        </div>

        {/* Scrollable Permissions */}
        <div className="flex-1 overflow-y-auto space-y-4 py-1">
          {Object.keys(permissions).map((category) => (
            <div
              key={category}
              className="border border-[#e6e6e6] p-4 rounded-[10px]"
            >
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-[600] text-[14px] text-[#252525] capitalize">
                  {category.replace(/([A-Z])/g, " $1")}
                </h3>
                <label className="flex items-center text-[14px] text-[#1b1b1b] font-[400]">
                  <input
                    type="checkbox"
                    checked={Object.values(permissions[category]).every(Boolean)}
                    onChange={() => handleSelectAll(category)}
                    className="form-checkbox h-[20px] w-[20px] text-green-600 border-[1px] border-[#d1d1d6] rounded focus:ring-green-500"
                  />
                  <span className="ml-2">Select All</span>
                </label>
              </div>

              <div className="grid grid-cols-4 gap-x-[29px] gap-y-[20px]">
                {Object.keys(permissions[category]).map((perm) => (
                  <label
                    key={perm}
                    className="flex items-center text-[14px] text-[#1b1b1b] font-[400] capitalize"
                  >
                    <input
                      type="checkbox"
                      checked={
                        permissions[category][perm as keyof PermissionSet]
                      }
                      onChange={() =>
                        handlePermissionChange(
                          category,
                          perm as keyof PermissionSet
                        )
                      }
                      className="form-checkbox h-[20px] w-[20px] text-green-600 border-[1px] border-[#d1d1d6] rounded focus:ring-green-500"
                    />
                    <span className="ml-2">{perm}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Sticky Bottom Buttons */}
        <div className="sticky bottom-0 bg-white py-4 flex justify-end space-x-3 border-t border-gray-200">
          <Button
            type="button"
            variant="text"
            size="large"
            onClick={onClose}
            className="w-[165px] h-[42px] whitespace-nowrap 
               !bg-transparent !border !border-[#16A34A] 
               !text-[#16A34A] font-medium rounded-[8px]"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="large"
            onClick={handleSubmit}
          >
            Create Role
          </Button>
        </div>
      </div>

      {/* ✅ Success Popup */}
      {showSuccess && (
        <SuccessPopup
          title="Role Created Successfully"
          subtitle="New role has been added and is now available for assignments."
          onClose={handlePopupClose}
          onConfirm={handlePopupClose}
          BtnName="Okay"
          successImage={null}
        />
      )}
    </>
  );
};

export default CreateRoleForm;
