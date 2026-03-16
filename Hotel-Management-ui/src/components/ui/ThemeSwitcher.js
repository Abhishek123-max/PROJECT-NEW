'use client';
import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';

const ThemeSwitcher = () => {
  const { currentTheme, switchTheme, themes, theme } = useTheme();
  
  return (
    <div className="absolute top-5 right-5 z-10">
      <select 
        value={currentTheme} 
        onChange={(e) => switchTheme(e.target.value)}
        className="px-3 py-2 border-2 rounded-md text-[14px] cursor-pointer focus:outline-none"
        style={{
          backgroundColor: theme.surface,
          color: theme.text,
          borderColor: theme.border
        }}
      >
        {Object.keys(themes).map((themeName) => (
          <option key={themeName} value={themeName}>
            {themeName.charAt(0).toUpperCase() + themeName.slice(1)}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ThemeSwitcher;