'use client';
import React from 'react';
import { Formik } from 'formik';
import * as Yup from 'yup';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { useTheme } from '@/contexts/ThemeContext';
import Dropdown from '@/components/ui/dropdown';
import { BankDetailsData } from '@/types/onboarding';

interface BankDetailsFormProps {
  onBack: () => void;
  onNext: (data: BankDetailsData) => void;
  initialValues?: BankDetailsData;
}

const accountTypes = [
  { value: 'Savings', label: 'Savings' },
  { value: 'Current', label: 'Current' },
  { value: 'Salary', label: 'Salary' },
];

const BankDetailsForm: React.FC<BankDetailsFormProps> = ({
  onBack,
  onNext,
  initialValues
}) => {
  const { theme } = useTheme();

  const ValidationSchema = Yup.object().shape({
    accountNumber: Yup.string()
      .required('Account Number is required')
      .matches(/^\d+$/, 'Account Number must contain only digits'),
    confirmAccountNumber: Yup.string()
      .required('Confirm Account Number is required')
      .matches(/^\d+$/, 'Confirm Account Number must contain only digits')
      .oneOf([Yup.ref('accountNumber')], 'Account numbers do not match'),
    accountHolderName: Yup.string().required('Account Holder Name is required'),
    accountType: Yup.string().required('Account Type is required'),
    branchName: Yup.string().required('Branch Name is required'),
    ifscCode: Yup.string().required('IFSC Code is required'),
  });

  return (
    <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-6xl mx-auto">
      <Formik
        initialValues={initialValues || {
          accountNumber: '',
          confirmAccountNumber: '',
          accountHolderName: '',
          accountType: '',
          branchName: '',
          ifscCode: '',
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
                Bank Details
              </h2>
              <p className="text-sm" style={{ color: theme.textSecondary }}>
                Enter your bank information
              </p>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <Input
                label="Account Number"
                name="accountNumber"
                placeholder="eg. 56777456534323"
                tooltip='100%'
                errori='92%'
                required
                value={values.accountNumber}
                onChange={(e) => {
                  const digitsOnly = e.target.value.replace(/\D/g, '');
                  setFieldValue('accountNumber', digitsOnly);
                }}
                onBlur={handleBlur}
                error={touched.accountNumber && errors.accountNumber}
                inputProps={{ inputMode: 'numeric', pattern: "\\d*" }}
              />
              <Input
                label="Confirm Account Number"
                name="confirmAccountNumber"
                placeholder="eg. 56777456534323"
                tooltip='100%'
                errori='92%'
                required
                value={values.confirmAccountNumber}
                onChange={(e) => {
                  const digitsOnly = e.target.value.replace(/\D/g, '');
                  setFieldValue('confirmAccountNumber', digitsOnly);
                }}
                onBlur={handleBlur}
                error={touched.confirmAccountNumber && errors.confirmAccountNumber}
                inputProps={{ inputMode: 'numeric', pattern: "\\d*" }}
              />
              <Input
                label="Account Holder Name"
                name="accountHolderName"
                placeholder="eg. Pawan Singh"
                tooltip='100%'
                errori='92%'
                required
                value={values.accountHolderName}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.accountHolderName && errors.accountHolderName}
              />

              {/* 🔹 Account Type Dropdown */}
              <div className="grid w-full mb-5 relative gap-[6px]">
                <label
                  className="block mb-[4px] font-semibold text-[14px]"
                  style={{ color: theme.text, ...(theme.typography || {}) }}
                >
                  Account Type <span style={{ color: theme.error }}>*</span>
                </label>
                <Dropdown
                  name="accountType"
                  value={values.accountType}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  options={accountTypes}
                  placeholder="Choose Account Type"
                  tooltip='95%'
                errori='88%'
                  theme={theme}
                  error={touched.accountType && (errors.accountType as string)}
                />
                
              </div>

              <Input
                label="Branch Name"
                name="branchName"
                placeholder="eg. Madiwala"
                tooltip='100%'
                errori='92%'
                required
                value={values.branchName}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.branchName && errors.branchName}
              />
              <Input
                label="IFSC Code"
                name="ifscCode"
                placeholder="eg. HDFC0004532"
                tooltip='100%'
                errori='92%'
                required
                value={values.ifscCode}
                onChange={handleChange}
                onBlur={handleBlur}
                error={touched.ifscCode && errors.ifscCode}
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

export default BankDetailsForm;
