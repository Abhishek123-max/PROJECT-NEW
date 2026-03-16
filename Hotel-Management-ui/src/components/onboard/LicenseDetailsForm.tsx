'use client';
import React from 'react';
import { Formik } from 'formik';
import * as Yup from 'yup';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { useTheme } from '@/contexts/ThemeContext';
import { LicenseDetailsData } from '@/types/onboarding';

interface LicenseDetailsFormProps {
  onBack: () => void;
  onNext: (data: LicenseDetailsData) => void;
  initialValues?: LicenseDetailsData;
}


const LicenseDetailsForm: React.FC<LicenseDetailsFormProps> = ({
  onBack,
  onNext,
  initialValues
}) => {
  const { theme } = useTheme();

  const ValidationSchema = Yup.object().shape({
    gstNumber: Yup.string()
      .required('GST Number is required')
      .length(15, 'GSTIN must be 15 characters long.')
      .matches(/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$/, 'Invalid GSTIN format.'),
    fssaiLicenseNo: Yup.string().required('FSSAI License Number is required'),
    tinNumber: Yup.string(),
    tradeLicense: Yup.string(),
    professionalTaxRegistrationNumber: Yup.string(),
  });

  return (
    <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-6xl mx-auto">
      <Formik
        initialValues={initialValues || {
          gstNumber: '',
          fssaiLicenseNo: '',
          tinNumber: '',
          tradeLicense: '',
          professionalTaxRegistrationNumber: '',
        }}
        validationSchema={ValidationSchema}
        onSubmit={(values) => {
          onNext(values);
        }}
      >
        {({ values, errors, touched, handleChange, handleBlur, handleSubmit, setFieldValue }) => (
          <form onSubmit={handleSubmit} className="w-full max-w-5xl space-y-6 mx-auto" style={{ background: theme.surface, color: theme.text }}>
            <div className="flex flex-col text-left">
              <h2 className="text-2xl font-bold" style={{ color: theme.text }}>
                License Details
              </h2>
              <p className="text-sm" style={{ color: theme.textSecondary }}>
                Enter your license information
              </p>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <Input
                label="GST Number"
                name="gstNumber"
                placeholder="eg. 22ABCDE1234F1Z5"
                tooltip='100%'
                errori='90%'
                required
                value={values.gstNumber}
                onChange={(e) => {
                  const formatted = e.target.value
                    .toUpperCase()
                    .replace(/[^A-Z0-9]/g, '')
                    .slice(0, 15);
                  setFieldValue('gstNumber', formatted);
                }}
                onBlur={handleBlur}
                error={touched.gstNumber && errors.gstNumber}
                inputProps={{
                  maxLength: 15,
                  pattern: "^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$",
                }}
              />
              <Input
                label="FSSAI License No."
                name="fssaiLicenseNo"
                placeholder="eg. 343454546423244"
                tooltip='100%'
                errori='90%'
                required
                value={values.fssaiLicenseNo}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.fssaiLicenseNo && errors.fssaiLicenseNo}
              />
              <Input
                label="TIN Number"
                name="tinNumber"
                placeholder="eg. 29654321098"
                tooltip='100%'
                errori='90%'
                value={values.tinNumber}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.tinNumber && errors.tinNumber}
              />
              <Input
                label="Trade License"
                name="tradeLicense"
                placeholder="eg. TL/BBMP/2025/04567"
                tooltip='100%'
                errori='90%'
                value={values.tradeLicense}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.tradeLicense && errors.tradeLicense}
              />
            </div>

            <div className='mt-6'>
              <Input
                label="Professional Tax Registration Number"
                name="professionalTaxRegistrationNumber"
                tooltip='100%'
                errori='90%'
                placeholder="eg. PTR/KA/567890"
                value={values.professionalTaxRegistrationNumber}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.professionalTaxRegistrationNumber && errors.professionalTaxRegistrationNumber}
              />
            </div>

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

export default LicenseDetailsForm;
