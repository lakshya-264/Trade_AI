import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';
import { 
  ShieldCheckIcon, 
  ArrowLeftIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const VerifyReset: React.FC = () => {
  const [params] = useSearchParams();
  const identifier = params.get('identifier') || '';
  const navigate = useNavigate();
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(60); // 1 minute in seconds
  const [canResend, setCanResend] = useState(false);

  useEffect(() => {
    if (!identifier) {
      toast.error('No identifier found. Please start over.');
      navigate('/forgot-password');
      return;
    }

    // Countdown timer
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [identifier, navigate]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleResend = async () => {
    setLoading(true);
    try {
      const isEmail = identifier.includes('@');
      const payload = isEmail ? { email: identifier } : { mobile_number: identifier };
      const response = await api.forgotPassword(payload);
      
      if (response.success) {
        toast.success('OTP resent successfully!');
        setTimeLeft(60); // Reset to 1 minute
        setCanResend(false);
      } else {
        toast.error(response.error || 'Failed to resend OTP');
      }
    } catch (err: any) {
      toast.error(err?.message || 'Failed to resend OTP');
    } finally {
      setLoading(false);
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length !== 6) {
      toast.error('Please enter a 6-digit OTP');
      return;
    }

    setLoading(true);
    try {
      const response = await api.verifyResetOtp(identifier, otp);
      
      if (response.success) {
        toast.success('OTP verified successfully!');
        setTimeout(() => {
          navigate(`/reset-password?identifier=${encodeURIComponent(identifier)}&otp=${encodeURIComponent(otp)}`);
        }, 500);
      } else {
        toast.error(response.error || 'Invalid OTP');
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Invalid OTP. Please try again.';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setOtp(value);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900/20 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Back Link */}
        <Link 
          to="/forgot-password" 
          className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 mb-6 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5" />
          <span>Back</span>
        </Link>

        {/* Card */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl shadow-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full mb-4">
              <ShieldCheckIcon className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Verify OTP
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Enter the 6-digit OTP sent to
            </p>
            <p className="text-sm font-medium text-gray-900 dark:text-white mt-1">
              {identifier}
            </p>
          </div>

          {/* Timer */}
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex items-center justify-center gap-2 text-blue-700 dark:text-blue-300">
              <ClockIcon className="h-5 w-5" />
              <span className="text-sm font-medium">
                OTP expires in: <span className="font-bold">{formatTime(timeLeft)}</span>
              </span>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Enter 6-Digit OTP
              </label>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                className="w-full px-4 py-3 text-center text-2xl font-bold tracking-widest border-2 border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="000000"
                value={otp}
                onChange={handleOtpChange}
                maxLength={6}
                required
                disabled={loading}
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={loading || otp.length !== 6}
              className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-3 px-4 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <ShieldCheckIcon className="h-5 w-5" />
                  <span>Verify OTP</span>
                </>
              )}
            </button>
          </form>

          {/* Resend OTP */}
          <div className="mt-6 text-center">
            {canResend ? (
              <button
                onClick={handleResend}
                disabled={loading}
                className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium text-sm disabled:opacity-50"
              >
                Resend OTP
              </button>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Didn't receive OTP? Resend available in {formatTime(timeLeft)}
              </p>
            )}
          </div>

          {/* Help Text */}
          <div className="mt-6 text-center">
            <Link 
              to="/forgot-password" 
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
            >
              Change email/mobile number
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyReset;


