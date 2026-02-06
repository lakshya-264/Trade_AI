import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import LoginModal from '../components/LoginModal';
import { toast } from 'react-hot-toast';

const Login: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(true);
  const reason = searchParams.get('reason');

  useEffect(() => {
    // Show appropriate message based on reason
    if (reason === 'session_invalidated') {
      toast.error('Your session has expired. Please login again.', {
        duration: 5000,
      });
    }
  }, [reason]);

  const handleClose = () => {
    setIsModalOpen(false);
    // Navigate to home after closing
    navigate('/');
  };

  const handleLoginSuccess = () => {
    setIsModalOpen(false);
    // Navigate to home after successful login
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-[#131722] flex items-center justify-center p-4">
      <LoginModal 
        isOpen={isModalOpen} 
        onClose={handleClose}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  );
};

export default Login;
