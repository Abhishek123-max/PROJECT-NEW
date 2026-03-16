'use client';
import React, { useEffect, useState } from 'react';
import { Stepper, Step, StepLabel, StepConnector, stepConnectorClasses } from '@mui/material';
import { styled } from '@mui/material/styles';
import BasicDetailsForm from '@/components/onboard/BasicDetailsForm';
import LocationDetailsForm from '@/components/onboard/LocationDetailsForm';
import LicenseDetailsForm from '@/components/onboard/LicenseDetailsForm';
import SocialMediaLinksForm from '@/components/onboard/SocialMediaLinksForm';
import BankDetailsForm from '@/components/onboard/BankDetailsForm';
import { OnboardingPayload, LocationDetailsData, LicenseDetailsData, BankDetailsData, BasicDetailsFormValues } from '@/types/onboarding';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

import { Stepper1, Stepper2, Stepper3, Stepper4, Stepper5 } from '@/assests/svgicons';

// ----------------------
// 🔹 Custom Styled Connector (to mimic your green line)
// ----------------------
const CustomConnector = styled(StepConnector)(() => ({
  [`&.${stepConnectorClasses.alternativeLabel}`]: {
    top: 22,
  },
  [`& .${stepConnectorClasses.line}`]: {
    height: 4,
    border: 0,
    backgroundColor: '#fff',
  },
  [`&.${stepConnectorClasses.active} .${stepConnectorClasses.line}`]: {
    backgroundColor: '#4ade80', // green-400
  },
  [`&.${stepConnectorClasses.completed} .${stepConnectorClasses.line}`]: {
    backgroundColor: '#4ade80',
  },
}));

// ----------------------
// 🔹 Custom Step Icon to match your existing icons
// ----------------------
const StepIcons: Record<number, React.FC> = {
  1: Stepper1,
  2: Stepper2,
  3: Stepper3,
  4: Stepper4,
  5: Stepper5,
};

function CustomStepIcon(props: { active: boolean; completed: boolean; icon: number }) {
  const { active, completed, icon } = props;
  const Icon = StepIcons[icon];

  return (
    <div
      className={`w-[40px] h-[40px] rounded-full flex items-center justify-center transition-all duration-300
        ${active
          ? 'border-1 border-green-500 text-green-500 shadow-lg bg-white'
          : completed
            ? 'bg-green-400 text-white'
            : 'bg-white'
        }`}
    >
      <Icon />
    </div>
  );
}

// ----------------------
// 🔹 Main Component
// ----------------------
export default function OnboardPage() {
  const { theme } = useTheme();
  const router = useRouter();
  const { getAccessToken, isTokenValid } = useAuth();
  const [step, setStep] = useState(0); // MUI uses 0-based indexing
  const [authorized, setAuthorized] = useState<boolean>(false);

  // Only allow access if access_token exists in localStorage
  useEffect(() => {
    try {
      const token = getAccessToken();
      if (!token || !isTokenValid(token)) {
        // Optional: clear invalid token
        try { localStorage.removeItem('access_token'); } 
        catch { router.replace('/');
        }
        router.replace('/');
      } else {
        setAuthorized(true);
      }
    } catch {
      router.replace('/');
    }
  }, [router, getAccessToken, isTokenValid]);

  const [basicDetails, setBasicDetails] = useState<BasicDetailsFormValues | null>(null);
  const [locationDetails, setLocationDetails] = useState<LocationDetailsData | null>(null);
  const [licenseDetails, setLicenseDetails] = useState<LicenseDetailsData | null>(null);
  const [bankDetails, setBankDetails] = useState<BankDetailsData | null>(null);

  const steps = [
    'Basic Details',
    'Location Details',
    'License Details',
    'Bank Details',
    'Social Media Links',
  ];

  type StepData =
    | BasicDetailsFormValues
    | LocationDetailsData
    | LicenseDetailsData
    | BankDetailsData
    | Partial<OnboardingPayload>;

  const handleNext = (data: StepData, currentStep: number) => {
    if (currentStep === 1) setBasicDetails(data as BasicDetailsFormValues);
    else if (currentStep === 2) setLocationDetails(data as LocationDetailsData);
    else if (currentStep === 3) setLicenseDetails(data as LicenseDetailsData);
    else if (currentStep === 4) setBankDetails(data as BankDetailsData);
    setStep((prev) => prev + 1);
  };

  const handleBack = () => setStep((prev) => prev - 1);

  if (!authorized) {
    return null; // or a loader if you prefer
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-4 py-10"
      style={{ background: theme.background }}
    >
      {/* 🔹 Heading */}
      <div className="text-center mb-8">
        <h1 className="text-[26px] font-bold" style={{ color: theme.text }}>
          Hotel Onboarding
        </h1>
        <p className="text-[14px] text-gray-500 mt-1">
          Enter your details to access your account.
        </p>
      </div>

      {/* 🔹 MUI Stepper (same layout & design preserved) */}
      <div className="w-full max-w-7xl mb-4">
        <Stepper alternativeLabel activeStep={step} connector={<CustomConnector />}>
          {steps.map((label, index) => (
            <Step key={label}>
              <StepLabel
                StepIconComponent={(props) => (
                  <CustomStepIcon
                    active={!!props.active}
                    completed={!!props.completed}
                    icon={index + 1}
                  />
                )}
              >
                <span
                  className={`mt-2 text-[14px] text-center block ${
                    step === index
                      ? 'font-semibold text-green-600'
                      : 'text-gray-500'
                  }`}
                >
                  {label}
                </span>
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </div>

      {/* 🔹 Step Forms */}
      {step === 0 && <BasicDetailsForm onNext={(data) => handleNext(data, 1)} initialValues={basicDetails ?? undefined} />}
      {step === 1 && (
        <LocationDetailsForm onBack={handleBack} onNext={(data) => handleNext(data, 2)} initialValues={locationDetails ?? undefined} />
      )}
      {step === 2 && (
        <LicenseDetailsForm onBack={handleBack} onNext={(data) => handleNext(data, 3)} initialValues={licenseDetails ?? undefined} />
      )}
      {step === 3 && (
        <BankDetailsForm onBack={handleBack} onNext={(data) => handleNext(data, 4)} initialValues={bankDetails ?? undefined} />
      )}
      {step === 4 && (
        <SocialMediaLinksForm
          onBack={handleBack}
          aggregated={{
            hotel_name: basicDetails?.hotelName ?? '',
            owner_name: basicDetails?.contactPerson ?? '',
            gst_number: licenseDetails?.gstNumber ?? '',
            business_type: basicDetails?.businessType ?? '',
            logo_url: '',
            logo: (basicDetails?.logo as File | null) ?? null,
            description: basicDetails?.description ?? '',
            address_line_1: locationDetails?.addressLine1 ?? '',
            address_line_2: locationDetails?.addressLine2 ?? '',
            area: locationDetails?.area ?? '',
            city: locationDetails?.city ?? '',
            pincode: locationDetails?.pinCode ?? '',
            state: locationDetails?.state ?? '',
            fssai_number: licenseDetails?.fssaiLicenseNo ?? '',
            tin_number: licenseDetails?.tinNumber ?? '',
            professional_tax_reg_number: licenseDetails?.professionalTaxRegistrationNumber ?? '',
            trade_license_number: licenseDetails?.tradeLicense ?? '',
            bank_details: bankDetails
              ? {
                  account_number: bankDetails.accountNumber,
                  account_holder_name: bankDetails.accountHolderName,
                  account_type: bankDetails.accountType,
                  branch_name: bankDetails.branchName,
                  ifsc_code: bankDetails.ifscCode,
                }
              : {},
            social_media_links: {},
          } as Partial<OnboardingPayload>}
        />
      )}
    </div>
  );
}
