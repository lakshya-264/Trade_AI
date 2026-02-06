import React, { useState, useEffect } from 'react';
import { XMarkIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { api } from '../services/api';

interface OTPVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onVerificationSuccess: () => void;
  phoneOrEmail: string;
  isEmail: boolean;
  purpose: string;
  onBack?: () => void;
}

const OTPVerificationModal: React.FC<OTPVerificationModalProps> = ({
  isOpen,
  onClose,
  onVerificationSuccess,
  phoneOrEmail,
  isEmail,
  purpose,
  onBack
}) => {
  const [otp, setOtp] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);
  const [canResend, setCanResend] = useState(false);

  // Countdown timer for resend
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => {
        setResendCooldown(resendCooldown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [resendCooldown]);

  // Start cooldown when modal opens
  useEffect(() => {
    if (isOpen) {
      setResendCooldown(60); // 60 seconds cooldown
      setCanResend(false);
      setOtp('');
      setError('');
    }
  }, [isOpen]);

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setOtp(value);
    if (error) setError('');
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await api.verifyOTP(phoneOrEmail, otp, purpose, isEmail);
      
      if (response.success) {
        onVerificationSuccess();
        onClose();
      } else {
        setError(response.error || 'OTP verification failed');
      }
    } catch (error: any) {
      console.error('OTP verification error:', error);
      setError(error.message || 'Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    if (!canResend) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await api.resendOTP(phoneOrEmail, purpose, isEmail);
      
      if (response.success) {
        setResendCooldown(60);
        setCanResend(false);
        setError('');
        // Show success message briefly
        setTimeout(() => setError(''), 3000);
      } else {
        setError(response.error || 'Failed to resend OTP');
      }
    } catch (error: any) {
      console.error('Resend OTP error:', error);
      setError(error.message || 'Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            {onBack && (
              <button
                onClick={onBack}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                <ArrowLeftIcon className="w-5 h-5" />
              </button>
            )}
            <h2 className="text-xl font-bold text-gray-900">
              Verify {isEmail ? 'Email' : 'Mobile Number'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Instructions */}
          <div className="mb-6">
            <p className="text-gray-600 mb-2">
              We've sent a 6-digit verification code to:
            </p>
            <p className="font-medium text-gray-900">
              {isEmail ? phoneOrEmail : `+91 ${phoneOrEmail}`}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Enter the code below to verify your {isEmail ? 'email' : 'mobile number'}.
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className={`mb-4 p-3 rounded-lg ${
              error.includes('sent') || error.includes('success') 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-red-50 border border-red-200'
            }`}>
              <p className={`text-sm ${
                error.includes('sent') || error.includes('success')
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}>
                {error}
              </p>
            </div>
          )}

          {/* OTP Form */}
          <form onSubmit={handleVerify} className="space-y-4">
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-2">
                Verification Code
              </label>
              <input
                type="text"
                id="otp"
                value={otp}
                onChange={handleOtpChange}
                placeholder="000000"
                className="w-full px-4 py-3 text-center text-2xl font-mono border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent tracking-widest"
                maxLength={6}
                autoComplete="one-time-code"
                required
              />
            </div>

            {/* Resend Section */}
            <div className="text-center">
              {canResend ? (
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={isLoading}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium disabled:opacity-50"
                >
                  Resend Code
                </button>
              ) : (
                <p className="text-gray-500 text-sm">
                  Resend code in {resendCooldown}s
                </p>
              )}
            </div>

            {/* Verify Button */}
            <button
              type="submit"
              disabled={otp.length !== 6 || isLoading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Verifying...' : 'Verify Code'}
            </button>
          </form>

          {/* Help Text */}
          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              Didn't receive the code? Check your {isEmail ? 'email' : 'SMS'} or{' '}
              <button
                onClick={handleResend}
                disabled={!canResend || isLoading}
                className="text-blue-600 hover:text-blue-700 disabled:opacity-50"
              >
                resend
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OTPVerificationModal;
