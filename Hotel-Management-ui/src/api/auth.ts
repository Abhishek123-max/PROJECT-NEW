import { httpClient } from '@/lib/request';
import { LoginCredentials, AuthResponse } from '@/types/auth';

export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      const apiResponse = await httpClient<AuthResponse>('/api/v1/auth/login', {
        method: 'POST',
        data: credentials,
      });

      // Map backend payload to our AuthResponse shape
      const mapped: AuthResponse = {
        success: Boolean(apiResponse?.success),
        message: apiResponse?.message,
        data: apiResponse?.data,
        user: apiResponse?.user,
        onboarding_completed: apiResponse?.onboarding_completed,
        reset_required: apiResponse?.reset_required,
      };

      return mapped;
    } catch (error: unknown) {
      let message = "Unknown error";
      if (error instanceof Error) {
        message = error.message;
      } else if (
        error &&
        typeof error === 'object' &&
        'message' in error &&
        typeof (error as { message: unknown }).message === 'string'
      ) {
        message = (error as { message: string }).message;
      }

      return { success: false, errors: { general: message } };
    }
  },
};
