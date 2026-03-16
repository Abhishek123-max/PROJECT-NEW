"use client";
import { useState } from "react";
import Button from "@/components/ui/Button";
import { CloseIcon } from "@/assests/icons";

const Drawer = ({ isOpen, onClose, title, children }) => {
  return (
    <div
      className={`fixed inset-0 z-50 transform ${
        isOpen ? "translate-x-0" : "translate-x-full"
      } transition-transform duration-300 ease-in-out`}
    >
      <div
        className="absolute inset-0 w-[527px] opacity-50 "
        onClick={onClose}
      ></div>
      <div className="fixed top-0 right-0 h-full w-[527px] md:w-[527px] bg-gray-50 shadow-lg overflow-y-auto">
        <div className="flex justify-between items-center p-4 bg-white ">
          <h2 className="text-xl font-semibold">{title}</h2>
        
          <Button onClick={onClose} className="!bg-white  hover:text-gray-700">
            <CloseIcon width="15px" height="15px" color="#708698" />
          </Button>
        </div>
        1<div className="p-4">{children}</div>
      </div>
    </div>
  );
};

export default Drawer;
