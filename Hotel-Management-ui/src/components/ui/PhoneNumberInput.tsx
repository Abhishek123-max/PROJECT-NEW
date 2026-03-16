import { useTheme } from "@/contexts/ThemeContext";
import React from 'react';
import PhoneInput from 'react-phone-input-2';
import 'react-phone-input-2/lib/material.css';

interface PhoneNumberInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string | boolean;
  label?: string;
  className?: string;
  width?: string;
  required?: boolean;
  tooltip?: string;
  errori?: string;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
}

const PhoneNumberInput: React.FC<PhoneNumberInputProps> = ({
  value,
  onChange,
  error,
  label = '',
  className = '',
  width = "100%",
  required = false,
  tooltip = '',
  errori = '',
  onBlur
}) => {
  const { theme } = useTheme();
  return (
    <div
      className={`grid w-[290px] mb-5 relative gap-[6px] ${className}`}
      style={{ width }}
    >
      {label && (
        <label
          className="block mb-[4px] font-semibold text-[14px]"
          style={{ color: theme.text, ...(theme.typography || {}) }}
        >
          {label} {required && <span style={{ color: theme.error }}>*</span>}
        </label>
      )}

      <div style={{ position: 'relative' }}>
        {/* Error alert above input (like Input.tsx) */}
        {error && (
          <div className="absolute -top-10 -translate-x-full z-10" style={{ left: tooltip }}>
            <div className="bg-red-500 text-white text-[13px] px-2.5 py-1.5 h-8 rounded-md shadow-md whitespace-nowrap">
              {error}
            </div>
            <span className="absolute right-6 top-6.5 w-2.5 h-2.5 bg-red-500 rotate-45"></span>
          </div>
        )}
        <PhoneInput
          country={'in'}
          value={value}
          onChange={(phone) => onChange(phone)} // just pass full phone
          disableCountryCode={false} // let the component manage the code
          countryCodeEditable={false}
          inputProps={{
            name: 'phone',
            required,
            autoFocus: false,
            onBlur: onBlur,
          }}
          inputStyle={{
            width: '100%',
            borderRadius: '8px',
            border: error ? '2px solid #EF4444' : '1.5px solid #e5e5e5ff',
            height: '48px',
            color: 'black',
            backgroundColor: 'white',
            boxShadow: error ?'0 0 5px 5px rgba(255, 77, 77, 0.2)' : 'none',
            fontSize: '16px',
            paddingLeft: '60px',
            transition: 'all 0.2s ease',
          }}
          buttonStyle={{
            border: 'none',
            background: 'transparent',
            paddingLeft: '12px',
            paddingRight: '8px',
          }}
          containerStyle={{
            width: '100%',
            borderRadius: '8px',
            background: 'transparent',
          }}
          specialLabel=""
          dropdownStyle={{
            borderRadius: '10px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          }}
        />

        {/* Only green focus if not error */}
        <style>{`
         .react-tel-input .form-control:focus {
           ${error ? '' : 'border-color: #59ff96e0 !important; box-shadow: 0 0 5px 1px #54ff4bbf !important;'}
         }
         .react-tel-input .selected-flag {
           background: #878E9614;
           border-radius: 15% !important;
         }
         .react-tel-input .flag-dropdown {
           background: transparent !important;
           border: none !important;
           padding-left: 0px !important;
         }
        `}</style>
      </div>
      <div className="absolute -bottom-[-20%] -translate-y-full" style={{ left: errori }}>
        {error && (
          <span className="w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">
            i
          </span>
        )}
      </div>

      {error && <div className="text-red-500 text-xs mt-1">{error}</div>}
    </div>
  );
};

export default PhoneNumberInput;
