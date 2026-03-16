export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenPayload {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserPayload {
  id: number;
  username: string;
  role: string;
  hotel_id: number;
  branch_id: number | null;
  zone_id: number | null;
  floor_id: number | null;
  section_id: number | null;
  is_active: boolean;
  feature_toggles?: Record<string, boolean>;
  last_login: string | null;
  created_at: string;
}

export interface AuthResponse {
  success: boolean;
  message?: string;
  data?: TokenPayload;
  user?: UserPayload;
  reset_required?: boolean;
  onboarding_completed?: boolean;
  errors?: { general?: string };
}