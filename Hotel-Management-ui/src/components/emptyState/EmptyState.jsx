"use client";
import React from "react";
import Image from "next/image";
import role from "../../assests/role.png";
import Link from "next/link";
import Button from "@/components/ui/Button";

const EmptyState = ({
  iconSrc,
  iconAlt,
  title,
  description,
  backButtonText,
  createButtonText,
  onCreateClick,
  onBackClick,
}) => {
  return (
    <div className="flex justify-center mt-[200px] min-h-screen bg-gray-50">
      <div className="flex flex-col items-center text-center p-6">
        {/* Image */}
        {iconSrc && (
          <Image
            src={iconSrc}
            alt={iconAlt}
            width={120}
            height={120}
            className="mb-[30px]"
          />
        )}
        {/* Title */}
        <h1 className="text-xl font-semibold text-gray-800 mb-2">{title}</h1>

        {/* Subtitle */}
        <p className="text-sm text-gray-400 mb-[47px]">{description}</p>

        {/* Buttons */}
        <div className="flex gap-4">
          {backButtonText && (
            <Button
              variant="text"
              size="large"
              className="w-[165px]"
              onClick={onBackClick}
            >
              {backButtonText}
            </Button>
          )}

          {createButtonText && (
            <Button variant="primary" size="large" onClick={onCreateClick}>
              {createButtonText}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmptyState;
