import React, { useState } from "react";

type Option = {
  value: string;
  label: string;
};

type DropdownProps = {
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  options: Option[];
  placeholder?: string;
  className?: string;
  theme: {
    surface: string;
    text: string;
    border: string;
  };
  error?: string | boolean;
  tooltip?: string;
  errori?: string;
  onBlur?: (e: React.FocusEvent<HTMLSelectElement>) => void;
};

const Dropdown: React.FC<DropdownProps> = ({
  name,
  value,
  onChange,
  options,
  placeholder = "Select option",
  theme,
  className = "",
  error = '',
  tooltip = '',
  errori = '',
  onBlur,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative w-full">
      {error && (
        <div className="absolute -top-10 -translate-x-full z-10" style={{ left: tooltip }}>
          <div className="bg-red-500 text-white text-[13px] px-2.5 py-1.5 h-8 rounded-md shadow-md whitespace-nowrap">
            {error}
          </div>
          <span className="absolute right-6 top-6.5 w-2.5 h-2.5 bg-red-500 rotate-45"></span>
        </div>
      )}
      <select
        name={name}
        value={value}
        onChange={onChange}
        onBlur={(e) => {
          if (onBlur) onBlur(e);
          setOpen(false);
        }}
        className={`w-full px-4 py-3 rounded-lg border-2 focus:outline-green-500 focus:shadow-[0_0_5px_1px_rgba(84,255,75,0.75)] appearance-none ${className}`}
        style={{
          backgroundColor: theme.surface,
          color: value ? theme.text : '#9CA3AF', // Gray color for placeholder
          borderColor: error ? '#EF4444' : theme.border,
          boxShadow: error ? '0 0 5px 5px rgba(255, 77, 77, 0.2)' : '',
          transition: 'border 0.2s, box-shadow 0.2s',
        }}
        onClick={() => setOpen((prev) => !prev)}
      >
        <option value="" style={{ color: '#9CA3AF' }}>
          {placeholder}
        </option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} style={{ color: theme.text }}>
            {opt.label}
          </option>
        ))}
      </select>
      {/* Red i info indicator when error */}
      <div className="absolute -bottom-1 -translate-y-full z-10" style={{ left: errori }}>
        {error && (
          <span className="w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">
            i
          </span>
        )}
      </div>
      {/* custom arrow */}
      <span
        className={`absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none 
                    transition-transform duration-200 ${
                      open ? "rotate-180" : ""
                    }`}
        style={{ color: theme.text }}
      >
        <svg
          width="13"
          height="8"
          viewBox="0 0 13 8"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12.7941 1.88681L11.3841 0.476807L6.79413 5.05681L2.20413 0.476807L0.794128 1.88681L6.79413 7.88681L12.7941 1.88681Z"
            fill="#0B0B12"
            fillOpacity="0.6"
          />
        </svg>
      </span>
    </div>
  );
};

export default Dropdown;
