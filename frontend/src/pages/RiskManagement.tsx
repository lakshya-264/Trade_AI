/**
 * Risk Management Page
 * Comprehensive risk management dashboard with portfolio risk tools
 */

import React from 'react';
import { cn } from '../lib/utils';
import RiskManagementDashboard from '../components/RiskManagementDashboard';

interface RiskManagementPageProps {
  className?: string;
}

const RiskManagementPage: React.FC<RiskManagementPageProps> = ({ className }) => {
  return (
    <div className={cn("h-screen flex flex-col", className)}>
      <RiskManagementDashboard />
    </div>
  );
};

export default RiskManagementPage;
