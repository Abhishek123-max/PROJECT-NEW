"use client";
import React, { useEffect } from "react";
import Image from "next/image";
import Button from "@/components/ui/Button";

const SuccessPopup = ({
  title,
  subtitle,
  onClose,
  onConfirm,
  BtnName,
  successImage,
}) => {
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [onClose]);
  return (
    <div className="fixed inset-0 bg-opacity-50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      {/* Popup Container */}
      <div className="relative rounded-[20px] shadow-xl w-[516px] flex flex-col overflow-hidden bg-white">
        {/* Gradient / Blur Container */}
        <div
          className="relative p-8 w-full h-[319px] overflow-hidden rounded-[16px]"
          style={{
            background: "#FFFFFF",
          }}
        >
          {/* Vector 4 (green gradient blur layer) */}
          <div
            style={{
              position: "absolute",
              width: "569px",
              height: "353px",
              left: "0px",
              top: "39px",
              background:
                "linear-gradient(131.84deg, #C5FFCC 1.01%, #C9FBCE 217.6%)",
              opacity: 0.55,
              filter: "blur(132px)",
              zIndex: 0,
            }}
          ></div>
          {/* Vector 5 (blue blur layer) */}
          <div
            style={{
              position: "absolute",
              width: "425px",
              height: "135px",
              left: "9px",
              top: "30px",
              background: "rgba(18, 145, 195, 0.39)",
              filter: "blur(107px)",
              zIndex: 1,
            }}
          ></div>
          {/* Card Content */}
          <div
            style={{
              position: "relative",
              zIndex: 2,
              backdropFilter: "blur(214px)",
              borderRadius: "16px",
            }}
          >
            {/* Close Button */}{" "}
            <Button
              onClick={onClose}
              className="absolute -top-8 -right-5 !text-[#708698] cursor-pointer !bg-white !rounded-full !p-1 transition"
              aria-label="Close"
            >
              {" "}
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                {" "}
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />{" "}
              </svg>{" "}
            </Button>
            {/* Success Image */}
            <div className="px-[14px] flex flex-col items-center justify-center flex-1 mt-3">
              <div className="rounded-full overflow-hidden p-1 flex items-center justify-center mb-6">
                <Image
                  src={successImage}
                  alt="Success"
                  className="w-[108px] h-[108px] object-contain"
                />
              </div>

              {/* Title */}
              <h3 className="text-black text-[26px] font-bold mb-2">{title}</h3>

              {/* Subtitle */}
              <p className="text-black text-[14px] font-medium text-center">
                {subtitle}
              </p>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="bg-white py-[22px] px-[18px] flex justify-center">
          <Button
            onClick={onConfirm}
            variant="primary"
            size="large"
            className="w-[177px]"
          >
            {BtnName}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SuccessPopup;
