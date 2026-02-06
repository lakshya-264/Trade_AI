/**
 * Intelligent Trading Page
 * Smart trading features dashboard with AI-powered recommendations
 */

import React from 'react';
import IntelligentTradingInterface from '../components/IntelligentTradingInterface';

interface IntelligentTradingPageProps {
  symbol?: string;
}

const IntelligentTradingPage: React.FC<IntelligentTradingPageProps> = ({ symbol }) => {
  return (
    <div className="h-screen flex flex-col">
      <IntelligentTradingInterface />
    </div>
  );
};

export default IntelligentTradingPage;