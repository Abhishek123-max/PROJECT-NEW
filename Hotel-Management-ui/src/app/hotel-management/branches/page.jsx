"use client";

import React from 'react';
import BranchCard from '@/components/hotel/BranchCard'
import Button from '@/components/ui/Button';

const branches = [
  {
    name: 'Hotel Empire',
    location: 'Koramangala',
    isMain: true,
    gstNumber: '3416251725FFHS3567',
    fssaiLicense: '23186723521',
    managerName: 'Pawan Singh',
    managerPhone: '+91 7877474454',
  },
  {
    name: 'Hotel Empire',
    location: 'BTM Layout',
    isMain: false,
    gstNumber: '3416251725FFHS3567',
    fssaiLicense: '23186723521',
    managerName: 'Pawan Singh',
    managerPhone: '+91 7877474454',
  },
  {
    name: 'Hotel Empire',
    location: 'Malleshwaram',
    isMain: false,
    gstNumber: '3416251725FFHS3567',
    fssaiLicense: '23186723521',
    managerName: 'Pawan Singh',
    managerPhone: '+91 7877474454',
  },
  {
    name: 'Hotel Empire',
    location: 'Banashankari',
    isMain: false,
    gstNumber: '3416251725FFHS3567',
    fssaiLicense: '23186723521',
    managerName: 'Pawan Singh',
    managerPhone: '+91 7877474454',
  },
  {
    name: 'Hotel Empire',
    location: 'Jayanagar',
    isMain: false,
    gstNumber: '3416251725FFHS3567',
    fssaiLicense: '23186723521',
    managerName: 'Pawan Singh',
    managerPhone: '+91 7877474454',
  },
  {
    name: 'Hotel Empire',
    location: 'HSR Layout',
    isMain: false,
    gstNumber: '3416251725FFHS3567',
    fssaiLicense: '23186723521',
    managerName: 'Pawan Singh',
    managerPhone: '+91 7877474454',
  },
];

const HotelBranches = () => {
  return (
    <div className="min-h-screen  p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-[22px] font-[700] text-[#17181A]">Hotel Branches</h2>
         <Button
            variant="primary"
            size="large"
            className="w-[165px] h-[42px] whitespace-nowrap"
          
          >
           Add Branch
          </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[20px]">
        {branches.map((branch, index) => (
          <BranchCard key={index} branch={branch} />
        ))}
      </div>
    </div>
  );
};



export default HotelBranches;