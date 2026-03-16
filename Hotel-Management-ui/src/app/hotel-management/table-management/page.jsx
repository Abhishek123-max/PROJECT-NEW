"use client";
import React, { useState } from "react";
import EmptyState from "@/components/emptyState/EmptyState";
import hotel from "@/assests/hotel.png";
import useNavigation from "@/hooks/useNavigation";
import CreateFloorForm from "@/components/hotel/floor/CreateFloorForm";
import FloorLists from "@/components/hotel/floor/FloorLists"

const TableManagement = () => {
  const { handleBack } = useNavigation();

  const [floors, setFloors] = useState([]); // Floor list state
  const [isFormOpen, setIsFormOpen] = useState(false); // Popup open/close

  const handleCreateFloor = () => setIsFormOpen(true);
  const handleCloseForm = () => setIsFormOpen(false);

  const handleAddFloor = (floorData) => {
    setFloors((prev) => [...prev, { id: Date.now(), ...floorData }]);
    setIsFormOpen(false);
  };

  return (
    <div className="p-6">
      {/* Floor List or EmptyState */}
      {/* {floors.length === 0 ? ( */}
        {/* <EmptyState
          iconSrc={hotel}
          iconAlt="No Floor Added"
          title="No Floor Added Yet"
          description={
            <>
              You haven’t added any Floor for this branch. Create a floor to start
              managing <br /> halls, sections, tables, and reservations
            </>
          }
          backButtonText="Back"
          createButtonText="Create Floor"
          onCreateClick={handleCreateFloor}
          onBackClick={handleBack}
        /> */}
      {/* ) : ( */}
        <div>
        <FloorLists/>
        </div>
      {/* )} */}

      {/* Create Floor Popup */}
      <CreateFloorForm
        isOpen={isFormOpen}
        onClose={handleCloseForm}
        onAdd={handleAddFloor}
      />
    </div>
  );
};

export default TableManagement;
