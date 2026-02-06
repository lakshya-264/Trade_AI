import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';
import { 
  EnvelopeIcon, 
  PhoneIcon, 
  ArrowLeftIcon,
  KeyIcon
} from '@heroicons/react/24/outline';

const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const isEmail = identifier.includes('@');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(false);
    
    try {
      const payload = isEmail ? { email: identifier } : { mobile_number: identifier };
      const response = await api.forgotPassword(payload);
      
      if (response.success) {
        toast.success(`OTP sent to your ${isEmail ? 'email' : 'mobile number'}!`);
        setSuccess(true);
        setTimeout(() => {
          navigate(`/verify-reset?identifier=${encodeURIComponent(identifier)}`);
        }, 1500);
      } else {
        toast.error(response.error || 'Failed to send OTP');
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to send OTP. Please try again.';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900/20 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Back to Login Link */}
        <Link 
          to="/dashboard" 
          className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 mb-6 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5" />
          <span>Back to Login</span>
        </Link>

        {/* Card */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl shadow-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mb-4">
              <KeyIcon className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Forgot Password?
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              No worries! Enter your email or mobile number and we'll send you an OTP to reset your password.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Email or Mobile Number
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  {isEmail ? (
                    <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <PhoneIcon className="h-5 w-5 text-gray-400" />
                  )}
                </div>
                <input
                  type="text"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder={isEmail ? "Enter your email" : "Enter your mobile number"}
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                {isEmail 
                  ? "We'll send a verification code to your email address"
                  : "We'll send a verification code to your mobile number"}
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !identifier.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 px-4 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Sending OTP...</span>
                </>
              ) : (
                <>
                  <KeyIcon className="h-5 w-5" />
                  <span>Send OTP</span>
                </>
              )}
            </button>
          </form>

          {/* Success Message */}
          {success && (
            <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <p className="text-sm text-green-800 dark:text-green-300 text-center">
                ✓ OTP sent successfully! Redirecting to verification page...
              </p>
            </div>
          )}

          {/* Help Text */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Remember your password?{' '}
              <Link 
                to="/dashboard" 
                className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          OTP will expire in 10 minutes. Please check your {isEmail ? 'email' : 'SMS'} inbox.
        </p>
      </div>
    </div>
  );
};

export default ForgotPassword;


