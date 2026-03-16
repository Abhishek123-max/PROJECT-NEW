export interface PermissionSet {
  create: boolean;
  view: boolean;
  edit: boolean;
  delete: boolean;
  import: boolean;
  export: boolean;
}

export interface RolePermissions {
  [key: string]: PermissionSet;
}

export interface CreateRoleRequest {
  name: string;
  display_name: string;
  description: string;
  level: number;
  can_create_roles: string[];
  permissions: RolePermissions;
}

export interface CreateRoleResponse {
  success: boolean;
  message?: string;
  data?: unknown;
  errors?: {
    general?: string;
  };
}



// types/roles.ts

export interface PermissionAction {
  create?: boolean;
  view?: boolean;
  edit?: boolean;
  delete?: boolean;
  import?: boolean;
  export?: boolean;
  [key: string]: boolean | undefined; // to handle keys like "role_management.view"
}

export interface Role {
  id: number;
  name: string;
  display_name: string;
  description: string;
  level: number;
  permissions: Record<string, PermissionAction>;
  can_create_roles: string[];
  default_features: Record<string, boolean>;
  is_default: boolean;
}

export interface RoleListResponse {
  roles: Role[];
}
