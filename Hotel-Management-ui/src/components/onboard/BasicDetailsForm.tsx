"use client";
import React, { useState } from "react";
import Image from "next/image";
import { Formik } from "formik";
import * as Yup from "yup";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
/* import ThemeSwitcher from "@/components/ui/ThemeSwitcher"; */
import { useTheme } from "@/contexts/ThemeContext";
import Dropdown from "@/components/ui/dropdown";
import { UploadImgLogo } from "@/assests/svgicons";
import PhoneNumberInput from '@/components/ui/PhoneNumberInput';
import { BasicDetailsFormValues } from "@/types/onboarding";


interface BasicDetailsFormProps {
  onNext: (data: BasicDetailsFormValues) => void;
  initialValues?: BasicDetailsFormValues;
}

const BasicDetailsForm = ({ onNext, initialValues }: BasicDetailsFormProps) => {
  const { theme } = useTheme();
  const [logoName, setLogoName] = useState<string | null>(null);
  const [logoError, setLogoError] = useState<string | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);

  // Restore logo preview when initialValues are provided (navigating back)
  React.useEffect(() => {
    if (initialValues?.logo && initialValues.logo instanceof File) {
      const reader = new FileReader();
      reader.onload = () => {
        setLogoPreview(reader.result as string);
      };
      reader.readAsDataURL(initialValues.logo);
      setLogoName(initialValues.logo.name);
    }
  }, [initialValues]);

  const ValidationSchema = Yup.object().shape({
    hotelName: Yup.string().required("Hotel / Business name is required"),
    businessType: Yup.string().required("Please select business type"),
    contactPerson: Yup.string().required("Contact person is required"),
    email: Yup.string().email("Please enter a valid email address"),
    phone: Yup.string().matches(/^\d{12,14}$/, "Enter a valid 12-14 digit phone number").required("Phone number is required"),
    description: Yup.string(),
    logo: Yup.mixed().required("Logo is required"),
  });

  return (
    <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-6xl mx-auto">
      <Formik
        initialValues={initialValues || {
          hotelName: "",
          businessType: "",
          contactPerson: "",
          email: "",
          phone: "",
          description: "",
          logo: null,
        }}
        validationSchema={ValidationSchema}
        onSubmit={(values) => {
          console.log('BasicDetailsForm submitted with values:', values);
          // Pass the preview image and logoName for now
          onNext({ ...values, logo: values.logo });
        }}
      >
      {({ values, errors, touched, handleChange, handleBlur, setFieldValue, handleSubmit }) => (
        <form onSubmit={handleSubmit} className="w-full max-w-5xl g-white space-y-6 mx-auto" style={{ background: theme.surface, color: theme.text }}>
        {/* Header */}
        <div className="flex flex-col text-left">
          <h2 className="text-2xl font-bold" style={{ color: theme.text }}>
            Basic Details
          </h2>
          <p className="text-sm" style={{ color: theme.textSecondary }}>
            Enter your basic business information to get started
          </p>
        </div>

        {/* Logo Upload */}
        <div className="flex flex-row items-start space-y-2 gap-5">
          <div className="py-2">
            {logoPreview ? (
              <Image
                src={logoPreview}
                alt="Logo preview"
                width={71}
                height={71}
                unoptimized
                className="max-w-[71px] max-h-[71px] rounded-md object-cover border border-green-200"
              />
            ) : (
              <UploadImgLogo />
            )}
          </div>
          <div className="w-[80%] py-2">
            <label
              className="font-semibold text-sm"
              style={{ color: theme.text }}
            >
              Logo
            </label>
            {/* Hidden native input */}
            <input
              id="logo"
              type="file"
              name="logo"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                // Keep image checking and preview logic as before
                setLogoError(null);
                if (!file) {
                  setLogoName(null);
                  setFieldValue('logo', null);
                  setLogoPreview(null);
                  return;
                }
                const maxBytes = 100 * 1024;
                if (file.size > maxBytes) {
                  setLogoError("Please upload square image, size less than 100KB");
                  setLogoName(null);
                  setFieldValue('logo', null);
                  return;
                }
                const img = new window.Image();
                const objectUrl = URL.createObjectURL(file);
                img.onload = () => {
                  const isSquare = img.width === img.height;
                  URL.revokeObjectURL(objectUrl);
                  if (!isSquare) {
                    setLogoError("Please upload square image, size less than 100KB");
                    setLogoName(null);
                    setFieldValue('logo', null);
                    setLogoPreview(null);
                    return;
                  }
                  setLogoError(null);
                  setLogoName(file.name);
                  setFieldValue('logo', file);
                  const reader = new FileReader();
                  reader.onload = () => {
                    setLogoPreview((reader.result as string) || null);
                  };
                  reader.readAsDataURL(file);
                };
                img.onerror = () => {
                  URL.revokeObjectURL(objectUrl);
                  setLogoError("Please upload square image, size less than 100KB");
                  setLogoName(null);
                  setFieldValue('logo', null);
                  setLogoPreview(null);
                };
                img.src = objectUrl;
              }}
              className="hidden"
            />
            {/* Custom file control */}
            <div className="flex items-center gap-3">
              <label
                htmlFor="logo"
                className="inline-flex items-center px-4 h-10 w-[40%] rounded-lg border cursor-pointer text-sm font-medium text-green-600 hover:bg-green-50"
              >
                Choose File
              </label>
              <span className="text-xs sm:text-sm italic text-gray-500 pr-10">
                {logoName ? (
                  <span className="text-gray-700 truncate max-w-[240px] inline-block align-middle">{logoName}</span>
                ) : (
                  'Please upload square image, size less than 100KB'
                )}
              </span>
            </div>
            {logoError && (
              <p className="mt-2 text-xs" style={{ color: theme.error }}>
                {logoError}
              </p>
            )}
            {touched.logo && errors.logo && (
              <p className="mt-2 text-xs" style={{ color: theme.error }}>
                {errors.logo}
              </p>
            )}
          </div>
          {/* Hotel Name */}
            <Input
              label="Hotel / Business Name"
              name="hotelName"
              placeholder="Enter your business name"
              required
              value={values.hotelName}
              onChange={handleChange}
              onBlur={handleBlur}
              error={touched.hotelName && errors.hotelName}
              tooltip="100%"
              errori="92%"
            />
        </div>

        {/* Business Type */}
        <div className="w-full flex flex-row items-start space-y-2 gap-5">
          <div className="w-full mb-5">
            <label
            className="block mb-[10px] font-semibold text-[14px]"
            style={{ color: theme.text, ...(theme.typography || {}) }}
          > 
              Business Type <span style={{ color: theme.error }}>*</span>
            </label>

            <Dropdown
              name="businessType"
              value={values.businessType}
              onChange={handleChange}
              onBlur={handleBlur}
              error={touched.businessType && errors.businessType}
              tooltip={'95%'}
              errori={'88%'}
              options={[
                { value: "hotel", label: "Hotel" },
                { value: "restaurant", label: "Restaurant" },
                { value: "cafe", label: "Café" },
                { value: "resort", label: "Resort" },
              ]}
              placeholder="Select type"
              theme={theme}
            />
            
          </div>

          {/* Contact Person */}
          <Input
            label="Contact Person"
            name="contactPerson"
            placeholder="Enter contact person name"
            required
            value={values.contactPerson}
            onChange={handleChange}
            onBlur={handleBlur}
            error={touched.contactPerson && errors.contactPerson}
            tooltip="100%"
            errori="92%"
          />
        </div>

        {/* Email */}
        <div className="w-full flex flex-row items-start space-y-2 gap-5">
          <Input
            label="Email Address"
            type="text"
            name="email"
            tooltip='100%'
            errori='92%'
            placeholder="Enter your email"
            value={values.email}
            onChange={handleChange}
            onBlur={handleBlur}
            error={touched.email && errors.email}
          />

          {/* Phone Number with Country Flag */}
          <PhoneNumberInput
            tooltip="100%"
            errori="92%"
            value={values.phone}
            onChange={phone => {
             
              setFieldValue('phone', phone);
            }}
            onBlur={handleBlur}
            error={touched.phone && errors.phone}
            label="Phone Number"
            required={true}
          />
        </div>

        {/* Description */}
        <Input
          name="description"
          label="Business Description"
          placeholder="Write a short description about your business..."
          value={values.description}
          onChange={handleChange}
          onBlur={handleBlur}
          error={touched.description && errors.description}
          style={{
            backgroundColor: theme.surface,
            color: theme.text,
            borderColor: theme.border,
          }}
        />
        {/* Submit */}
        <div className="flex justify-end pt-4">
          <Button className="w-[154px] h-[42px]" type="submit">
            Next
          </Button>
        </div>
      </form>
      )}
      </Formik>
    </div>
  );
};

export default BasicDetailsForm;
