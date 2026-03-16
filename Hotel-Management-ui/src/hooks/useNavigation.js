"use client";
import { useRouter } from "next/navigation";

export default function useNavigation() {
  const router = useRouter();

  const handleCreateRole = () => {
    router.push("/role-management/role/create-role");
  };

  const handleAddEmployee=()=>{
    router.push("/role-management/role/create-role");
  }

  const handleBack = () => {
    router.back(); 
  };

 return {
    handleCreateRole,
    handleBack,
    handleAddEmployee
   
  };
}
