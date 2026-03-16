import { httpClient } from '@/lib/request';
import { OnboardingPayload, OnboardingResponse } from '@/types/onboarding';

export const onboardingService = {
  submit: async (payload: OnboardingPayload): Promise<OnboardingResponse> => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const formData = new FormData();
      // Append primitives
      formData.append('name', payload.hotel_name || '');
      formData.append('owner_name', payload.owner_name || '');
      formData.append('gst_number', payload.gst_number || '');
      formData.append('business_type', payload.business_type || '');
      formData.append('description', payload.description || '');
      formData.append('address_line_1', payload.address_line_1 || '');
      formData.append('address_line_2', payload.address_line_2 || '');
      formData.append('area', payload.area || '');
      formData.append('city', payload.city || '');
      formData.append('pincode', payload.pincode || '');
      formData.append('state', payload.state || '');
      formData.append('fssai_number', payload.fssai_number || '');
      formData.append('tin_number', payload.tin_number || '');
      formData.append('professional_tax_reg_number', payload.professional_tax_reg_number || '');
      formData.append('trade_license_number', payload.trade_license_number || '');

      // Optional logo URL if backend expects it, but prefer file if present
      if (payload.logo_url) formData.append('logo_url', payload.logo_url);
      if (payload.logo instanceof File) {
        formData.append('logo', payload.logo);
      }

      // Append nested objects using bracket notation so backend gets normal fields
      const appendNested = (prefix: string, obj: Record<string, unknown>) => {
        Object.entries(obj || {}).forEach(([key, value]) => {
          const field = `${prefix}[${key}]`;
          if (Array.isArray(value)) {
            value.forEach((item) => {
              formData.append(`${field}[]`, item != null ? String(item) : '');
            });
          } else if (value instanceof File) {
            formData.append(field, value);
          } else if (value != null && typeof value === 'object') {
            // Shallow stringify for nested objects if any
            formData.append(field, JSON.stringify(value));
          } else {
            formData.append(field, value != null ? String(value) : '');
          }
        });
      };

      appendNested('bank_details', (payload.bank_details as Record<string, unknown>) || {});
      appendNested('social_media_links', (payload.social_media_links as Record<string, unknown>) || {});

      const response = await httpClient<OnboardingResponse>('/api/v1/hotels/onboarding', {
        method: 'PUT',
        data: formData,
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          // Do not set Content-Type here; the browser will add the correct multipart boundary
        },
      });
      return response;
      
    } catch (error: unknown) {
      return { success: false, errors: { general: (error as { message: string }).message } };
    }
  },
};


