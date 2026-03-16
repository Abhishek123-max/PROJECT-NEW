'use client';
import React, { useState, useEffect } from 'react';
import Snackbar from '@mui/material/Snackbar';
import MuiAlert, { AlertColor } from '@mui/material/Alert';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/contexts/ThemeContext';
import LoginForm from '@/components/LoginForm';
// import ThemeSwitcher from '@/components/ui/ThemeSwitcher';
import { LoginImg, Logo } from '@/assests/svgicons';
import LoadingCircle from '@/components/ui/LoadingCircle';

export default function LoginPage() {
  const { theme } = useTheme();
  const router = useRouter();
  const [toast, setToast] = useState<{ message: string; type?: AlertColor } | null>(null);
  const [toastOpen, setToastOpen] = useState(false);
  const [loadingSuperAdmin, setLoadingSuperAdmin] = useState(false);

  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 3000);
      setToastOpen(true);
      return () => clearTimeout(t);
    }
  }, [toast]);
  
  const handleLoginSuccess = (user: { username: string }) => {
    setToast({ message: `Welcome ${user.username}! Login successful.`, type: 'success' });
  };
  
  const handleSuperAdmin = () => {
    setLoadingSuperAdmin(true);
    setToast({ message: 'Redirecting to Super Admin login…', type: 'info' });
    setTimeout(() => {
      setLoadingSuperAdmin(false);
      router.push('/super-admin/login');
    }, 1600);
  };
  
  return (
    <div className="flex min-h-screen items-center justify-center w-full p-4 bg-gradient-to-br from-slate-50 to-slate-100" style={{ background: theme.background }}>
      <Snackbar
        open={toastOpen && Boolean(toast)}
        autoHideDuration={3000}
        onClose={() => setToastOpen(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MuiAlert
          elevation={6}
          variant="filled"
          onClose={() => setToastOpen(false)}
          severity={toast?.type || 'info'}
          sx={{ width: '100%' }}
        >
          {toast?.message}
        </MuiAlert>
      </Snackbar>
      {/* <ThemeSwitcher /> */}
         {/* Header with Logo */}
         <div className='container max-w-[760px] max-h-[590px] mx-auto'>
      <header className="justify-center">
        <div className='flex justify-center'>
        <Logo backgroundColor={theme.primary} /></div>
      </header>
      
      {/* Main Content */}
      <main className="w-full">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          <div className="flex justify-center">
            {/* Left Side: Illustration */}
              <div className="flex-1 bg-gradient-to-br from-[#506E5412] to-[#506E5412]">
                  <LoginImg backgroundColor={theme.primary} />
              </div>
            
            {/* Right Side: Login Form */}
            <div className="flex-1 lg:py-[30px] lg:px-[50px] items-center justify-center">
                <LoginForm 
                  onSuccess={handleLoginSuccess}
                />
            </div>
          </div>
        </div>
      </main>
      <div className="font-poppins">
      <button
  type="button"
  className="super-admin-link mt-5 w-full cursor-pointer border-none bg-none text-center text-md font-semibold no-underline hover:underline flex items-center justify-center gap-2"
  onClick={handleSuperAdmin}
  style={{ color: theme.primary }}
  disabled={loadingSuperAdmin}
>
  Are you a Super Admin?
  {loadingSuperAdmin && <LoadingCircle className="ml-2" size={20} />}
</button></div>
      
      </div>
      </div>
   
  );
}
     