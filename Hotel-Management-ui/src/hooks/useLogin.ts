import { useState } from 'react';
import { authService } from '@/api/auth';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

interface LoginErrors {
  general?: string;
  username?: string;
  password?: string;
}

export const useLogin = () => {
  const router = useRouter();
  const { validateCredentials: validateCreds } = useAuth();
  const [loading, setLoading] = useState<boolean>(false);
  const [errors, setErrors] = useState<LoginErrors>({});
  
  const validateCredentials = (username: string, password: string) => {
    const newErrors = validateCreds(username, password);
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const login = async (username: string, password: string) => {
    if (!validateCredentials(username, password)) {
      return { success: false, errors };
    }
    
    setLoading(true);
    setErrors({});
    
    try {
      const result = await authService.login({ username, password });

      if (result.success && result.data?.access_token) {
        // Store tokens securely (localStorage for now; consider cookies/HTTPOnly for production)
        localStorage.setItem('access_token', result.data.access_token);
        if (result.data.refresh_token) {
          localStorage.setItem('refresh_token', result.data.refresh_token);
        }
        console.log(">>>>>>>>>>>>>>>>>",result.onboarding_completed)
        // Optionally store user info
        if (result.user) {
          localStorage.setItem('user', JSON.stringify(result.user));
        }
        if (result.onboarding_completed === true) {
          router.push('/dashboard');
        } else {
          router.push('/onboarding');
        }
        setLoading(true);
        return { success: true, user: result.user };
      } else {
        setLoading(false);
        setErrors(result.errors || { general: result.message || 'Login failed.' });
        return { success: false, errors: result.errors };
      }
    } catch (error: unknown) {
      setLoading(false);
      let errorMessage = 'Login failed. Please try again.';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (
        error &&
        typeof error === 'object' &&
        'message' in error &&
        typeof (error as { message: unknown }).message === 'string'
      ) {
        errorMessage = (error as { message: string }).message;
      }
      setErrors({ general: errorMessage });
      return { success: false, errors: { general: errorMessage } };
    }
  };
  
  const clearErrors = () => {
    setErrors({});
  };
  
  return {
    login,
    loading,
    errors,
    clearErrors
  };
};
