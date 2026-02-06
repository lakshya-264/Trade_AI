import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';
import { 
  LockClosedIcon, 
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const ResetPassword: React.FC = () => {
  const [params] = useSearchParams();
  const identifier = params.get('identifier') || '';
  const otp = params.get('otp') || '';
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!identifier || !otp) {
      toast.error('Invalid reset link. Please start over.');
      navigate('/forgot-password');
    }
  }, [identifier, otp, navigate]);

  const validatePassword = (pwd: string) => {
    const minLength = pwd.length >= 8;
    const hasUpper = /[A-Z]/.test(pwd);
    const hasLower = /[a-z]/.test(pwd);
    const hasNumber = /[0-9]/.test(pwd);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(pwd);
    
    return {
      minLength,
      hasUpper,
      hasLower,
      hasNumber,
      hasSpecial,
      isValid: minLength && hasUpper && hasLower && hasNumber && hasSpecial
    };
  };

  const passwordValidation = validatePassword(password);
  const passwordsMatch = password === confirm && confirm.length > 0;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!passwordValidation.isValid) {
      toast.error('Password does not meet requirements');
      return;
    }
    
    if (password !== confirm) {
      toast.error('Passwords do not match');
      return;
    }

    setLoading(true);
    setSuccess(false);
    
    try {
      const response = await api.resetPassword(identifier, otp, password);
      
      if (response.success) {
        toast.success('Password reset successful!');
        setSuccess(true);
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
      } else {
        toast.error(response.error || 'Failed to reset password');
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to reset password. Please try again.';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900/20 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Card */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl shadow-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full mb-4">
              <LockClosedIcon className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Set New Password
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Create a strong password to secure your account
            </p>
          </div>

          {/* Success Message */}
          {success && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-center gap-2 text-green-800 dark:text-green-300">
                <CheckCircleIcon className="h-5 w-5" />
                <span className="text-sm font-medium">Password reset successful! Redirecting to login...</span>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={submit} className="space-y-6">
            {/* New Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                New Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LockClosedIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  className="w-full pl-10 pr-10 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="Enter new password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              
              {/* Password Requirements */}
              {password && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300">Password must contain:</p>
                  <div className="space-y-1 text-xs">
                    <div className={`flex items-center gap-2 ${passwordValidation.minLength ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}`}>
                      <span>{passwordValidation.minLength ? '✓' : '○'}</span>
                      <span>At least 8 characters</span>
                    </div>
                    <div className={`flex items-center gap-2 ${passwordValidation.hasUpper ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}`}>
                      <span>{passwordValidation.hasUpper ? '✓' : '○'}</span>
                      <span>One uppercase letter</span>
                    </div>
                    <div className={`flex items-center gap-2 ${passwordValidation.hasLower ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}`}>
                      <span>{passwordValidation.hasLower ? '✓' : '○'}</span>
                      <span>One lowercase letter</span>
                    </div>
                    <div className={`flex items-center gap-2 ${passwordValidation.hasNumber ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}`}>
                      <span>{passwordValidation.hasNumber ? '✓' : '○'}</span>
                      <span>One number</span>
                    </div>
                    <div className={`flex items-center gap-2 ${passwordValidation.hasSpecial ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}`}>
                      <span>{passwordValidation.hasSpecial ? '✓' : '○'}</span>
                      <span>One special character</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LockClosedIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type={showConfirm ? "text" : "password"}
                  className={`w-full pl-10 pr-10 py-3 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:border-transparent transition-all ${
                    confirm && passwordsMatch
                      ? 'border-green-500 focus:ring-green-500'
                      : confirm && !passwordsMatch
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
                  }`}
                  placeholder="Confirm new password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showConfirm ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              {confirm && (
                <p className={`mt-2 text-xs ${passwordsMatch ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {passwordsMatch ? '✓ Passwords match' : '✗ Passwords do not match'}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !passwordValidation.isValid || !passwordsMatch}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-4 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Resetting Password...</span>
                </>
              ) : (
                <>
                  <LockClosedIcon className="h-5 w-5" />
                  <span>Reset Password</span>
                </>
              )}
            </button>
          </form>

          {/* Help Text */}
          <div className="mt-6 text-center">
            <Link 
              to="/dashboard" 
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
            >
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;


