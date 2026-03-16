/* 'use client';
import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';

const Logo = ({ size = 'medium', showText = true }) => {
  const { theme } = useTheme();
  
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return { iconSize: '20px', fontSize: '16px' };
      case 'large':
        return { iconSize: '32px', fontSize: '24px' };
      default:
        return { iconSize: '24px', fontSize: '18px' };
    }
  };
  
  const { iconSize, fontSize } = getSizeStyles();
  
  return (
    <div className="flex items-center gap-2 font-semibold" style={{ color: theme.primary }}>
      <div 
        className="rounded-[6px] flex items-center justify-center text-[12px]"
        style={{ 
          backgroundColor: theme.primary,
          color: theme.surface,
          width: iconSize,
          height: iconSize
        }}
      >
        🍽
      </div>
      {showText && <span style={{ fontSize }}>DineFlow</span>}
    </div>
  );
};

export default Logo; */