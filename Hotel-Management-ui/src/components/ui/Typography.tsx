"use client";
import React, { ElementType } from 'react';

type TypographyVariant =
  | 'displayLarge'
  | 'displayMedium'
  | 'displaySmall'
  | 'headlineLarge'
  | 'headlineMedium'
  | 'headlineSmall'
  | 'titleLarge'
  | 'titleMedium'
  | 'titleSmall'
  | 'labelLarge'
  | 'labelMedium'
  | 'labelSmall'
  | 'bodyLarge'
  | 'bodyMedium'
  | 'bodySmall';

interface TypographyProps {
  variant: TypographyVariant;
  children: React.ReactNode;
  className?: string;
  color?: string;
  as?: ElementType;
}

const variantToDefaults: Record<TypographyVariant, { as: ElementType; classes: string }> = {
  displayLarge: { as: 'h1', classes: 'text-[26px] md:text-4xl font-bold' },
  displayMedium: { as: 'h2', classes: 'text-2xl font-bold' },
  displaySmall: { as: 'h3', classes: 'text-lg font-semibold' },
  headlineLarge: { as: 'h1', classes: 'text-4xl md:text-5xl font-bold leading-tight' },
  headlineMedium: { as: 'h2', classes: 'text-3xl md:text-4xl font-bold leading-snug' },
  headlineSmall: { as: 'h3', classes: 'text-2xl md:text-3xl font-semibold' },
  titleLarge: { as: 'h2', classes: 'text-xl md:text-2xl font-semibold' },
  titleMedium: { as: 'h3', classes: 'text-lg md:text-xl font-semibold' },
  titleSmall: { as: 'h4', classes: 'text-base md:text-lg font-semibold' },
  labelLarge: { as: 'span', classes: 'text-sm md:text-base font-semibold uppercase tracking-wide' },
  labelMedium: { as: 'span', classes: 'text-xs md:text-sm font-medium uppercase tracking-wide' },
  labelSmall: { as: 'span', classes: 'text-[10px] md:text-xs font-medium uppercase tracking-wide' },
  bodyLarge: { as: 'p', classes: 'text-base md:text-lg font-normal' },
  bodyMedium: { as: 'p', classes: 'text-sm md:text-base font-normal' },
  bodySmall: { as: 'p', classes: 'text-xs md:text-sm font-normal' },
};

const Typography: React.FC<TypographyProps> = ({ variant, children, className, color, as }) => {
  const { as: defaultAs, classes } = variantToDefaults[variant];
  const Component = as || defaultAs;

  return (
    <Component
      className={[classes, className].filter(Boolean).join(' ')}
      style={color ? { color } : undefined}
    >
      {children}
    </Component>
  );
};

export default Typography;


