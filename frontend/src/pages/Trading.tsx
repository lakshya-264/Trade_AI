import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

const Trading: React.FC = () => {
  const navigate = useNavigate();
  
  useEffect(() => {
    // Redirect to Comprehensive Trading Pro page
    navigate('/comprehensive-trading-pro', { replace: true });
  }, [navigate]);
  
  return null;
};

export default Trading;
