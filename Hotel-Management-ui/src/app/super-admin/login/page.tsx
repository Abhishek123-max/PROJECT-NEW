'use client';
import React from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/contexts/ThemeContext';
import LoginForm from '@/components/LoginForm';
import ThemeSwitcher from '@/components/ui/ThemeSwitcher';
import { LoginImg1, Logo } from '@/assests/svgicons';

export default function LoginPage() {
  const { theme } = useTheme();
  const router = useRouter();
  
  const handleLoginSuccess = (user: { username: string }) => {
    console.log('Login successful:', user);
    // Redirect to dashboard or store user data
    // router.push('/dashboard');
    /* alert(`Welcome ${user.username}! Login successful.`); */
  };
  
  const handleSuperAdmin = () => {
    // Navigate to super admin login or show modal
    alert('Super Admin functionality would be implemented here.');
    router.push('/super-admin/login');  
  };
  
  return (
    <div className="min-h-screen w-full p-4 bg-gradient-to-br from-slate-50 to-slate-100" style={{ background: theme.background }}>
      <ThemeSwitcher />
         {/* Header with Logo */}
      <header className="justify-center">
        <div className='flex justify-center'>
        <Logo backgroundColor={theme.primary} /></div>
      </header>
      
      {/* Main Content */}
      <main className="w-full max-w-4xl mx-auto ">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          <div className="flex justify-center">
            {/* Left Side: Illustration */}
              <div className="flex-1 bg-gradient-to-br from-green-50 to-green-100">
                  <LoginImg1 backgroundColor={theme.primary} />
              </div>
            
            {/* Right Side: Login Form */}
            <div className="flex-1 p-8 lg:p-12 flex items-center justify-center">
                <LoginForm 
                  onSuccess={handleLoginSuccess}
                  onSuperAdmin={handleSuperAdmin}
                />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
     