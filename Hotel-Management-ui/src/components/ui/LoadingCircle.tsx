import React from 'react';

interface LoadingCircleProps {
  size?: number; // both height and width, in px
  className?: string;
}

// A green loading spinner (circular)
const LoadingCircle: React.FC<LoadingCircleProps> = ({ size = 40, className = '' }) => {
  return (
    <span
      className={`inline-block animate-spin border-4 border-[#2FAC3E] border-t-transparent rounded-full ${className}`}
      style={{ width: size, height: size, borderWidth: size / 10 }}
      role="status"
      aria-label="Loading"
    />
  );
};

export default LoadingCircle;
