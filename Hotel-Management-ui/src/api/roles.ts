import { httpClient } from "@/lib/request";
import {
  CreateRoleRequest,
  CreateRoleResponse,
  RoleListResponse,
} from "@/types/roles";

export const roleService = {
  // ✅ Create new role
  createRole: async (payload: CreateRoleRequest): Promise<CreateRoleResponse> => {
    try {
      const apiResponse = await httpClient<CreateRoleResponse>("/api/v1/staff/roles", {
        method: "POST",
        data: payload,
      });

      const mapped: CreateRoleResponse = {
        success: Boolean(apiResponse?.success),
        message: apiResponse?.message,
        data: apiResponse?.data,
      };

      return mapped;
    } catch (error: unknown) {
      let message = "Unknown error";
      if (error instanceof Error) {
        message = error.message;
      } else if (
        error &&
        typeof error === "object" &&
        "message" in error &&
        typeof (error as { message: unknown }).message === "string"
      ) {
        message = (error as { message: string }).message;
      }

      return { success: false, errors: { general: message } };
    }
  },

  // ✅ Fetch all roles
  getAllRoles: async (): Promise<RoleListResponse> => {
    try {
      const apiResponse = await httpClient<RoleListResponse>("/api/v1/staff/roles", {
        method: "GET",
      });
      return apiResponse;
    } catch (error: unknown) {
      console.error("Error fetching roles:", error);
      throw new Error("Failed to fetch roles");
    }
  },
};
