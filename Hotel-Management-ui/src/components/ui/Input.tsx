"use client";
import React, { useState, forwardRef } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import { Eye, EyeOff } from "lucide-react";
import TextField, { TextFieldProps } from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";

// 🔹 Define Props for Input
interface InputProps extends Omit<TextFieldProps, "error"> {
  label?: string;
  type?: string;
  placeholder?: string;
  error?: boolean | string;
  required?: boolean;
  tooltip?:string;
  errori?:string;
  className?: string;
  showPasswordToggle?: boolean;
  width?: string;
  height?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      type = "text",
      placeholder,
      error,
      required = false,
      tooltip = '',
      errori = '',
      className = '',
      showPasswordToggle = false,
      width = "100%",
      height = "48px",
      ...props
    },
    ref
  ) => {
    const { theme } = useTheme();
    const [showPassword, setShowPassword] = useState(false);

    const inputType =
      showPasswordToggle && type === "password"
        ? showPassword
          ? "text"
          : "password"
        : type;

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

        {/* 🔴 Error alert above input */}
        {error && (
          <div className="absolute -top-3 -translate-x-full" style={{ left: `${tooltip}` }}>
            <div className="bg-red-500 text-white text-[13px] px-2.5 py-1.5 h-8 rounded-md shadow-md whitespace-nowrap">
              {typeof error === "string"
                ? error
                : "You have entered an invalid details"}
            </div>
            {/* Little arrow below alert */}
            <span className="absolute right-6 top-6.5 w-2.5 h-2.5 bg-red-500 rotate-45"></span>
          </div>
        )}

        <TextField
          inputRef={ref}
          type={inputType}
          placeholder={placeholder}
          error={!!error}
          variant="outlined"
          fullWidth
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: "10px",
              height,
              backgroundColor: theme.surface,
              color: theme.text,
              boxShadow: error
                ? "0 0 5px 5px rgba(255, 77, 77, 0.2)" // 🔴 red glow when error
                : "0 1px 3px rgba(0, 0, 0, 0)", // default subtle shadow
              transition: "all 0.3s ease",
              "& fieldset": {
                borderColor: error ? theme.error : theme.border,
                borderWidth: "2px",
              },
              "&:hover fieldset": {
                borderColor: error ? theme.error : theme.border,
              },
              "&.Mui-focused fieldset": {
                borderColor: error ? theme.error : theme.secondary,
                borderWidth: '2px',
                boxShadow: error 
                  ? 'none' // No green glow when there's an error
                  : theme.secondary
                    ? '0 0 5px 1px rgba(84, 255, 75, 0.75)' // Green glow only when no error
                    : 'none',
                transition: 'all 0.3s ease',
              },
            },
          }}
          InputProps={{
            endAdornment: (
              <>
                {/* Password Toggle */}
                {showPasswordToggle && type === "password" && (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      size="small"
                      sx={{ color: theme.textSecondary }}
                    >
                      {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                    </IconButton>
                  </InputAdornment>
                )}
              </>
            ),
          }}
          {...props}
        />
        <div className="absolute -bottom-1 -translate-y-full" style={{ left: `${errori}` }}>
          {/* Error Tooltip with Red i */}
          {error && (
            
              <span className="w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">
                i
              </span>
        
          )}
        </div>
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
