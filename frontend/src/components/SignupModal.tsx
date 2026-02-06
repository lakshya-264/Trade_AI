import React, { useState } from 'react';
import { XMarkIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import OTPVerificationModal from './OTPVerificationModal';

interface SignupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
  onSignupSuccess: (username: string) => void;
}

const SignupModal: React.FC<SignupModalProps> = ({
  isOpen,
  onClose,
  onSwitchToLogin,
  onSignupSuccess
}) => {
  const { signup } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    mobileNumber: '',
    password: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [pendingSignupData, setPendingSignupData] = useState<{
    username: string;
    email: string;
    mobileNumber: string;
    password: string;
  } | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const validateForm = () => {
    if (!formData.username.trim()) {
      setError('Username is required');
      return false;
    }
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!formData.email.includes('@')) {
      setError('Please enter a valid email');
      return false;
    }
    if (formData.mobileNumber.trim() && !/^[6-9]\d{9}$/.test(formData.mobileNumber.replace(/\D/g, ''))) {
      setError('Please enter a valid 10-digit Indian mobile number');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    setError('');

    try {
      // Store signup data for after OTP verification
      const signupData = {
        username: formData.username.trim(),
        email: formData.email.trim(),
        mobileNumber: formData.mobileNumber.trim(),
        password: formData.password
      };
      setPendingSignupData(signupData);

      // Send OTP for verification
      let otpSent = false;
      let lastError: string | null = null;
      
      // Send email OTP
      try {
        const emailResponse = await api.sendOTP(signupData.email, 'signup', true);
        console.log('Email OTP response:', emailResponse);
        if (emailResponse && emailResponse.success) {
          otpSent = true;
          console.log('Email OTP sent successfully');
        } else {
          console.warn('Email OTP response missing success flag:', emailResponse);
          lastError = emailResponse?.error || emailResponse?.message || 'Email OTP failed';
        }
      } catch (emailError: any) {
        console.error('Email OTP error:', emailError);
        lastError = emailError?.message || 'Failed to send email OTP';
      }

      // Send SMS OTP if mobile number provided
      if (signupData.mobileNumber) {
        try {
          const smsResponse = await api.sendOTP(signupData.mobileNumber, 'signup', false);
          console.log('SMS OTP response:', smsResponse);
          if (smsResponse && smsResponse.success) {
            otpSent = true;
            console.log('SMS OTP sent successfully');
          } else {
            console.warn('SMS OTP response missing success flag:', smsResponse);
            if (!otpSent) {
              lastError = smsResponse?.error || smsResponse?.message || 'SMS OTP failed';
            }
          }
        } catch (smsError: any) {
          console.error('SMS OTP error:', smsError);
          if (!otpSent) {
            lastError = smsError?.message || 'Failed to send SMS OTP';
          }
        }
      }

      if (otpSent) {
        // Show OTP verification modal
        setShowOTPModal(true);
      } else {
        setError(lastError || 'Failed to send verification code. Please try again.');
      }
    } catch (error) {
      console.error('Signup error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOTPVerificationSuccess = async () => {
    if (!pendingSignupData) return;

    setIsLoading(true);
    setError('');

    try {
      const success = await signup(
        pendingSignupData.username,
        pendingSignupData.email,
        pendingSignupData.password,
        pendingSignupData.mobileNumber || undefined
      );

      if (success) {
        // Signup successful
        onSignupSuccess(pendingSignupData.username);
        onClose();
        // Reset form
        setFormData({
          username: '',
          email: '',
          mobileNumber: '',
          password: '',
          confirmPassword: ''
        });
        setPendingSignupData(null);
      } else {
        setError('Signup failed. Username or email may already exist.');
      }
    } catch (error) {
      console.error('Signup error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOTPModalClose = () => {
    setShowOTPModal(false);
    setPendingSignupData(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Create Account</h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Username */}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="Enter your username"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Enter your email"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Mobile Number */}
          <div>
            <label htmlFor="mobileNumber" className="block text-sm font-medium text-gray-700 mb-1">
              Mobile Number <span className="text-gray-500 text-xs">(Optional)</span>
            </label>
            <input
              type="tel"
              id="mobileNumber"
              name="mobileNumber"
              value={formData.mobileNumber}
              onChange={handleInputChange}
              placeholder="Enter your 10-digit mobile number"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              maxLength={10}
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter without country code (e.g., 9876543210)
            </p>
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? (
                  <EyeSlashIcon className="w-5 h-5" />
                ) : (
                  <EyeIcon className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
              Confirm Password
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                placeholder="Confirm your password"
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showConfirmPassword ? (
                  <EyeSlashIcon className="w-5 h-5" />
                ) : (
                  <EyeIcon className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                "flex-1 px-4 py-2 text-white rounded-lg transition-colors",
                isLoading
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              )}
            >
              {isLoading ? 'Creating Account...' : 'Sign Up'}
            </button>
          </div>

          {/* Switch to Login */}
          <div className="text-center pt-2">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Sign In
              </button>
            </p>
          </div>
        </form>
      </div>

      {/* OTP Verification Modal */}
      {showOTPModal && pendingSignupData && (
        <OTPVerificationModal
          isOpen={showOTPModal}
          onClose={handleOTPModalClose}
          onVerificationSuccess={handleOTPVerificationSuccess}
          phoneOrEmail={pendingSignupData.mobileNumber || pendingSignupData.email}
          isEmail={!pendingSignupData.mobileNumber}
          purpose="signup"
        />
      )}
    </div>
  );
};

export default SignupModal;
