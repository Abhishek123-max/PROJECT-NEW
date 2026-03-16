"use client";
import React, { useEffect } from "react";
import Button from "@/components/ui/Button";
import { CloseIcon } from "@/assests/icons";

const Popup = ({
  onClose,
  children,
  className = "",
  containerClassName = "",
  inline = false,
}) => {
  // Handle Escape key for both inline + fullscreen
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

  if (inline) {
    
    return (
      <div
        className={`absolute bg-white rounded-lg  shadow-lg ${containerClassName}`}
      >
        <Button
          onClick={onClose}
          className="absolute !top-2 !right-2 !text-[#708698] cursor-pointer !bg-[#f1f1f1] !rounded-full !p-1 transition"
          aria-label="Close"
        >
          <CloseIcon width="14px" height="14px" color="#708698" />
        </Button>
        <div className={`${className} p-2`}>{children}</div>
      </div>
    );
  }

  // 👇 full modal
  return (
    <div
      className={`fixed inset-0 flex items-center justify-center bg-[#FFFFFFB2] backdrop-blur-sm p-4 z-50 ${containerClassName}`}
    >
      <div
        className={`relative rounded-[20px] bg-white flex flex-col overflow-hidden ${className}`}
        style={{ boxShadow: "0px 0px 110px 0px #30396D21" }}
      >
        <Button
          onClick={onClose}
          className="absolute !top-4 !right-4 !text-[#708698] cursor-pointer !bg-[#f1f1f1] !rounded-full !p-1 transition"
          aria-label="Close"
        >
          <CloseIcon width="15px" height="15px" color="#708698" />
        </Button>

        <div className="px-[14px] ">{children}</div>
      </div>
    </div>
  );
};

export default Popup;
