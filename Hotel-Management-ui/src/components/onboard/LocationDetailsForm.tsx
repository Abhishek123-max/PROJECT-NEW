'use client';
import React from 'react';
import { Formik } from 'formik';
import * as Yup from 'yup';
import Input from '@/components/ui/Input'; // ✅ the Input.tsx we made earlier
import Dropdown from '@/components/ui/dropdown';
import { useTheme } from '@/contexts/ThemeContext';
import Button from '@/components/ui/Button';
import { LocationDetailsData } from '@/types/onboarding';

interface LocationDetailsFormProps {
  onBack: () => void;
  onNext: (data: LocationDetailsData) => void;
  initialValues?: LocationDetailsData;
}

const states = [
  { value: 'Karnataka', label: 'Karnataka' },
  { value: 'Maharashtra', label: 'Maharashtra' },
  { value: 'Tamil Nadu', label: 'Tamil Nadu' },
  { value: 'Delhi', label: 'Delhi' }
];

const countries = [
  { value: 'India', label: 'India' },
  { value: 'USA', label: 'USA' },
  { value: 'UK', label: 'UK' },
  { value: 'UAE', label: 'UAE' }
];

const LocationDetailsForm: React.FC<LocationDetailsFormProps> = ({
  onBack,
  onNext,
  initialValues
}) => {
  const { theme } = useTheme();

  const ValidationSchema = Yup.object().shape({
    addressLine1: Yup.string().required("Address Line 1 is required"),
    addressLine2: Yup.string().required("Address Line 2 is required"),
    area: Yup.string().required("Area is required"),
    city: Yup.string().required("City is required"),
    state: Yup.string().required("State is required"),
    country: Yup.string().required("Country is required"),
    pinCode: Yup.string().matches(/^\d{6}$/, 'Pin Code must be 6 digits').required("Pin Code is required"),
  });

  return (
    <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-6xl mx-auto">
      <Formik
        initialValues={initialValues || {
          addressLine1: '',
          addressLine2: '',
          area: '',
          city: '',
          state: '',
          country: '',
          pinCode: '',
        }}
        validationSchema={ValidationSchema}
        onSubmit={(values) => {
          onNext(values);
        }}
      >
        {({ values, errors, touched, handleChange, handleBlur, handleSubmit, setFieldValue }) => (
          <form onSubmit={handleSubmit} className="w-full max-w-5xl space-y-6 mx-auto" style={{ background: theme.surface, color: theme.text }}>
            {/* Header */}
            <div className="flex flex-col text-left">
              <h2 className="text-2xl font-bold" style={{ color: theme.text }}>
                Location Details
              </h2>
              <p className="text-sm" style={{ color: theme.textSecondary }}>
                Enter your location information to get started
              </p>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <Input
                label="Address Line 1"
                name="addressLine1"
                placeholder="eg. Empire Hotel, No. 45"
                tooltip='100%'
                errori='90%'
                required
                value={values.addressLine1}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.addressLine1 && errors.addressLine1}
              />
              <Input
                label="Address Line 2"
                name="addressLine2"
                placeholder="eg. Koramangala 5th Block"
                tooltip='100%'
                errori='90%'
                required
                value={values.addressLine2}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.addressLine2 && errors.addressLine2}
              />
              <Input
                label="Area"
                name="area"
                placeholder="eg. Koramangala"
                tooltip='100%'
                errori='90%'
                required
                value={values.area}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.area && errors.area}
              />
              <Input
                label="City"
                name="city"
                placeholder="eg. Bangalore"
                tooltip='100%'
                errori='90%'
                required
                value={values.city}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.city && errors.city}
              />
            </div>

            {/* 🔹 State, Country, and Pin Code in a single row */}
            <div className="grid grid-cols-3 gap-[20px] mt-6">
              {/* State Dropdown */}
              <div className="grid w-full mb-5 relative gap-[6px]">
                <label
                  className="block mb-[4px] font-semibold text-[14px]"
                  style={{ color: theme.text, ...(theme.typography || {}) }}
                >
                  State <span style={{ color: theme.error }}>*</span>
                </label>
                <Dropdown
                  name="state"
                  value={values.state}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  options={states}
                  placeholder="eg. Karnataka"
                  theme={theme}
                  error={touched.state && errors.state}
                  tooltip={'95%'}
                  errori={'84%'}
                />
              </div>

              {/* Country Dropdown */}
              <div className="grid w-full mb-5 relative gap-[6px]">
                <label
                  className="block mb-[4px] font-semibold text-[14px]"
                  style={{ color: theme.text, ...(theme.typography || {}) }}
                >
                  Country <span style={{ color: theme.error }}>*</span>
                </label>
                <Dropdown
                  name="country"
                  value={values.country}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  options={countries}
                  placeholder="eg. India"
                  theme={theme}
                  error={touched.country && errors.country}
                  tooltip={'95%'}
                  errori={'84%'}
                />
              </div>

              {/* Pin Code Input */}
              <Input
                label="Pin Code"
                name="pinCode"
                placeholder="eg. 560078"
                tooltip='100%'
                errori='90%'
                required
                value={values.pinCode}
                onChange={(e) => {
                  const onlyDigits = e.target.value.replace(/\D/g, '').slice(0, 6);
                  setFieldValue('pinCode', onlyDigits);
                }}
                onBlur={handleBlur}
                error={touched.pinCode && errors.pinCode}
                inputProps={{ maxLength: 6, inputMode: 'numeric', pattern: "\\d{6}" }}
              />
            </div>
            {/* 🔹 Navigation Buttons */}
            <div className="flex justify-end gap-5 mt-8">
              <Button 
                className='w-[151px] h-[42px]'
                variant="text"
                onClick={onBack}
                sx={{ bgcolor: 'var(--Light, #E0F3E2)', color: theme.secondary, borderRadius: '8px', px: 4, py: 1, height: '42px', width: '151px' }}
              >
                Back
              </Button>
              <Button 
                className='w-[151px] h-[42px]'
                variant="contained"
                type="submit"
                sx={{
                  backgroundColor: theme.primary,
                  borderRadius: '8px',
                  px: 4,
                  py: 1,
                  height: '42px', width: '151px'
                }}
              >
                Next
              </Button>
            </div>
          </form>
        )}
      </Formik>
    </div>
  );
};

export default LocationDetailsForm;
