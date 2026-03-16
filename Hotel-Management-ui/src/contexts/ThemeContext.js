'use client';
import React, { createContext, useContext, useState } from 'react';
import { themes } from '@/lib/theme';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState('green');
  
  const theme = themes[currentTheme];
  
  const switchTheme = (themeName) => {
    setCurrentTheme(themeName);
  };
  
  return (
    <ThemeContext.Provider value={{ theme, currentTheme, switchTheme, themes }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};