import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosRequestHeaders } from 'axios';

// Use proxy for development to avoid CORS, or direct URL for production
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  
});

export const httpClient = async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  try {
    const response: AxiosResponse<T> = await axiosInstance(url, config);
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error) && error.response) {
      // Try to extract message from response data
      const msg = typeof error.response.data === 'object' && error.response.data && 'message' in error.response.data
        ? (error.response.data as { message?: string }).message
        : undefined;
      throw new Error(msg || 'Something went wrong');
    } else {
      let msg = 'Something went wrong';
      if (error instanceof Error) {
        msg = error.message;
      } else if (
        error &&
        typeof error === 'object' &&
        'message' in error &&
        typeof (error as { message: unknown }).message === 'string'
      ) {
        msg = (error as { message: string }).message;
      }
      throw new Error(msg);
    }
  }
};

// -------------------------
// Auth Interceptors
// -------------------------

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

const getAccessToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
};

const getRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
};

const setAccessToken = (token: string) => {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', token);
};

// Attach Authorization header if available
axiosInstance.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    const headers: AxiosRequestHeaders = {
      ...(config.headers as AxiosRequestHeaders | undefined),
      Authorization: `Bearer ${token}`,
    } as AxiosRequestHeaders;
    config.headers = headers;
  }
  return config;
});

// Handle 401 -> refresh token -> retry original request
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!error || !error.response) {
      return Promise.reject(error);
    }

    const { config, response } = error as { config: AxiosRequestConfig & { _retry?: boolean }; response: AxiosResponse };

    if (response.status !== 401 || config._retry) {
      return Promise.reject(error);
    }

    // Mark to avoid infinite loop on retry failures
    config._retry = true;

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      return Promise.reject(error);
    }

    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = (async () => {
        try {
          const refreshResponse = await axiosInstance.post<{ access_token?: string; refresh_token?: string;}>(
            '/api/v1/auth/refresh',
            { refresh_token: refreshToken }
          );
          const newAccessToken = refreshResponse.data?.access_token || null;
          if (newAccessToken) {
            setAccessToken(newAccessToken);
          }
          // Update refresh token if backend returns it in any common key
          if (typeof window !== 'undefined') {
            const newRefresh = refreshResponse.data?.refresh_token;
            if (newRefresh) {
              localStorage.setItem('refresh_token', newRefresh);
            }
          }
          return newAccessToken || null;
        } catch {
          return null;
        } finally {
          isRefreshing = false;
        }
      })();
    }

    const newToken = await refreshPromise;

    if (!newToken) {
      return Promise.reject(error);
    }

    // Retry original request with new token
    const headers: AxiosRequestHeaders = {
      ...(config.headers as AxiosRequestHeaders | undefined),
      Authorization: `Bearer ${newToken}`,
    } as AxiosRequestHeaders;
    config.headers = headers;
    return axiosInstance(config);
  }
);
