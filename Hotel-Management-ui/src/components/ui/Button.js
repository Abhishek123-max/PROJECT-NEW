'use client';
import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  disabled = false, 
  loading = false, 
  className = '', 
  ...props 
}) => {
  const { theme } = useTheme();
  
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: disabled ? theme.textSecondary : theme.primary,
          color: theme.surface,
          border: 'none'
        };
      case 'secondary':
        return {
          backgroundColor: 'transparent',
          color: theme.primary,
          border: `2px solid ${theme.primary}`
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: theme.text,
          border: `2px solid ${theme.border}`
        };
      case 'text': // 🆕 added
      return {
        backgroundColor: theme.button2,
        color: theme.primary,
        border: 'none',
      };
      default:
        return {
          backgroundColor: theme.primary,
          color: theme.surface,
          border: 'none'
        };
    }
  };
  
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return { padding: '8px 16px', fontSize: '12px' };
      case 'large':
        return { padding: '10px 40px', fontSize: '14px' };
      default:
        return { padding: '12px 24px', fontSize: '16px' };
    }
  };
  
  return (
    <button
      className={`rounded-[10px] font-semibold transition-all duration-200 flex items-center justify-center border border-red-500 disabled:cursor-not-allowed ${className}`}
      disabled={disabled || loading}
      style={{
        ...getVariantStyles(),
        ...getSizeStyles(),
        opacity: disabled ? 0.6 : 1,
        cursor: disabled || loading ? 'not-allowed' : 'pointer'
      }}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};

export default Button;