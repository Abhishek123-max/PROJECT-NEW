import React, { useState, useEffect } from 'react';
import { Formik } from 'formik';
import * as Yup from 'yup';
import { UserPayload } from '@/types/auth';
import { useTheme } from '@/contexts/ThemeContext';
import { useLogin } from '@/hooks/useLogin';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

interface LoginFormProps {
  onSuccess?: (user: UserPayload) => void;
  onSuperAdmin?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onSuperAdmin }) => {
  const { theme } = useTheme();
  const { login, loading, errors, clearErrors } = useLogin();
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string }>({ open: false, message: '' });

  useEffect(() => {
    if (errors.general) {
      setSnackbar({ open: true, message: errors.general });
      const timer = setTimeout(() => setSnackbar({ open: false, message: '' }), 4000);
      return () => clearTimeout(timer);
    }
  }, [errors.general]);

  const ValidationSchema = Yup.object().shape({
    username: Yup.string()
    .required('Username is required')
    .email('Enter a valid email address'),
    password: Yup.string()
      .required('Password is required')
      .min(6, 'Password must be at least 6 characters'),
  });

  const handleLogin = async (values: { username: string; password: string }) => {
    const result = await login(values.username, values.password);
    if (result.success && result.user) {
      onSuccess?.(result.user);
    }
  };

  return (
    <div className="mx-auto w-full">
      <Formik
        initialValues={{ username: '', password: '' }}
        validationSchema={ValidationSchema}
        onSubmit={handleLogin}
      >
        {({ values, errors: formikErrors, touched, handleChange, handleBlur, handleSubmit }) => (
          <form className="w-full" onSubmit={handleSubmit}>
            <h1 className="mb-2 text-[18px] font-bold" style={{ color: theme.text }}>Login</h1>
            <p className="mb-10 text-sm" style={{ color: theme.textSecondary }}>
              Enter your details to access your account.
            </p>
            {snackbar.open && (
              <div
                style={{
                  position: 'fixed',
                  bottom: 32,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: theme.error,
                  color: '#fff',
                  padding: '14px 32px',
                  borderRadius: '8px',
                  fontWeight: 500,
                  fontSize: '14px',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
                  zIndex: 9999,
                }}
              >
                {snackbar.message}
              </div>
            )}
            <Input
              name="username"
              label="Username"
              placeholder="Enter username"
              width="100%"
              height="50px"
              tooltip='115%'
              errori='102%'
              value={values.username}
              onChange={(e) => {
                handleChange(e);
                if ('username' in errors) clearErrors();
              }}
              onBlur={handleBlur}
              error={touched.username && formikErrors.username}
              required
            />
            <Input
              name="password"
              type="password"
              label="Password"
              placeholder="Password"
              tooltip='115%'
              errori='102%'
              value={values.password}
              onChange={(e) => {
                handleChange(e);
                if ('password' in errors) clearErrors();
              }}
              onBlur={handleBlur}
              error={touched.password && formikErrors.password}
              width="100%"
              height="50px"
              required
              showPasswordToggle
            />
            <Button
              className='w-full mt-8'
              type="submit"
              loading={loading}
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
            {onSuperAdmin && (
              <button
                type="button"
                onClick={onSuperAdmin}
                className="mt-4 w-full text-sm font-semibold underline"
                style={{ color: theme.secondary }}
              >
                Super Admin Login
              </button>
            )}
          </form>
        )}
      </Formik>
    </div>
  );
};

export default LoginForm;
