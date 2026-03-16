export interface OnboardingPayload {
  hotel_name: string;
  owner_name: string;
  gst_number: string;
  business_type: string;
  logo_url: string;
  logo?: File | null;
  description: string;
  address_line_1: string;
  address_line_2: string;
  area: string;
  city: string;
  pincode: string;
  state: string;
  fssai_number: string;
  tin_number: string;
  professional_tax_reg_number: string;
  trade_license_number: string;
  bank_details: Record<string, unknown>;
  social_media_links: Record<string, unknown>;
}

export interface OnboardingResponse {
  success: boolean;
  message?: string;
  data?: string;
  errors?: { general?: string };
}

export interface BasicDetailsFormValues {
  hotelName: string;
  businessType: string;
  contactPerson: string;
  email?: string;
  phone: string;
  description?: string;
  logo?: File | null;
}

export interface BankDetailsData {
  accountNumber: string;
  confirmAccountNumber: string;
  accountHolderName: string;
  accountType: string;
  branchName: string;
  ifscCode: string;
}

export interface LicenseDetailsData {
  gstNumber: string;
  fssaiLicenseNo: string;
  tinNumber: string;
  tradeLicense: string;
  professionalTaxRegistrationNumber: string;
}


export interface LocationDetailsData {
  addressLine1: string;
  addressLine2: string;
  area: string;
  city: string;
  state: string;
  country: string;
  pinCode: string;
}

export interface SocialMediaLinksData {
  googleReviewLink: string;
  youtubeLink: string;
  instagramLink: string;
  xLink: string;
  facebookLink: string;
  website: string;
}