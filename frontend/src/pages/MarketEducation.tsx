/**
 * Market Education Page
 * Unified page for all market education modules:
 * - IPO Markets
 * - Central Pivot Range (CPR)
 * - Regulators
 * - Corporate Actions
 * - Dow Theory
 * - Clearing & Settlement
 * - Glossary
 * - Level 3 Data
 * - Trading Routine
 * - Rights/OFS/FPO
 */

import React, { useState } from 'react';
import {
  BookOpenIcon,
  CalculatorIcon,
  ChartBarIcon,
  AcademicCapIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import IPOMarketsModule from '../components/education/IPOMarketsModule';
import CPRModule from '../components/education/CPRModule';
import RegulatorsModule from '../components/education/RegulatorsModule';
import CorporateActionsModule from '../components/education/CorporateActionsModule';
import DowTheoryModule from '../components/education/DowTheoryModule';
import ClearingSettlementModule from '../components/education/ClearingSettlementModule';
import GlossaryModule from '../components/education/GlossaryModule';
import Level3DataModule from '../components/education/Level3DataModule';
import TradingRoutineModule from '../components/education/TradingRoutineModule';
import RightsOFSPOModule from '../components/education/RightsOFSPOModule';

interface EducationModule {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  component: React.ComponentType;
  category: 'fundamentals' | 'technical' | 'tools' | 'reference';
}

const MarketEducation: React.FC = () => {
  const [activeModule, setActiveModule] = useState<string | null>(null);

  const modules: EducationModule[] = [
    {
      id: 'ipo-markets',
      name: 'IPO Markets',
      description: 'Complete guide to IPO process, analysis, and investing',
      icon: ChartBarIcon,
      component: IPOMarketsModule,
      category: 'fundamentals'
    },
    {
      id: 'cpr',
      name: 'Central Pivot Range',
      description: 'CPR calculation and trading strategies',
      icon: CalculatorIcon,
      component: CPRModule,
      category: 'technical'
    },
    {
      id: 'regulators',
      name: 'Regulators & Market Structure',
      description: 'SEBI, RBI, and market participants',
      icon: AcademicCapIcon,
      component: RegulatorsModule,
      category: 'fundamentals'
    },
    {
      id: 'corporate-actions',
      name: 'Corporate Actions',
      description: 'Dividends, splits, bonus, rights with impact calculators',
      icon: CalculatorIcon,
      component: CorporateActionsModule,
      category: 'fundamentals'
    },
    {
      id: 'dow-theory',
      name: 'Dow Theory',
      description: 'Dow Theory principles and pattern detection',
      icon: ChartBarIcon,
      component: DowTheoryModule,
      category: 'technical'
    },
    {
      id: 'clearing-settlement',
      name: 'Clearing & Settlement',
      description: 'T+1 settlement, pay-in/pay-out process',
      icon: DocumentTextIcon,
      component: ClearingSettlementModule,
      category: 'fundamentals'
    },
    {
      id: 'glossary',
      name: 'Glossary',
      description: 'Comprehensive stock market terms dictionary',
      icon: MagnifyingGlassIcon,
      component: GlossaryModule,
      category: 'reference'
    },
    {
      id: 'level3-data',
      name: 'Level 3 Data',
      description: 'Order book depth and market depth analysis',
      icon: ChartBarIcon,
      component: Level3DataModule,
      category: 'technical'
    },
    {
      id: 'trading-routine',
      name: 'Trading Routine',
      description: 'Daily, weekly, monthly trading checklists',
      icon: ClipboardDocumentListIcon,
      component: TradingRoutineModule,
      category: 'tools'
    },
    {
      id: 'rights-ofs-fpo',
      name: 'Rights, OFS & FPO',
      description: 'Understanding rights issues, OFS, and FPO',
      icon: BookOpenIcon,
      component: RightsOFSPOModule,
      category: 'fundamentals'
    }
  ];

  const categories = {
    fundamentals: 'Market Fundamentals',
    technical: 'Technical Analysis',
    tools: 'Trading Tools',
    reference: 'Reference'
  };

  const ActiveComponent = activeModule 
    ? modules.find(m => m.id === activeModule)?.component 
    : null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Market Education
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Comprehensive stock market education based on Zerodha Varsity modules
          </p>
        </div>

        {!activeModule ? (
          /* Module Selection Grid */
          <div className="space-y-8">
            {Object.entries(categories).map(([categoryKey, categoryName]) => {
              const categoryModules = modules.filter(m => m.category === categoryKey);
              if (categoryModules.length === 0) return null;

              return (
                <div key={categoryKey}>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                    {categoryName}
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {categoryModules.map((module) => {
                      const Icon = module.icon;
                      return (
                        <button
                          key={module.id}
                          onClick={() => setActiveModule(module.id)}
                          className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow text-left group"
                        >
                          <div className="flex items-start gap-4">
                            <div className="flex-shrink-0">
                              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center group-hover:bg-blue-200 dark:group-hover:bg-blue-800 transition-colors">
                                <Icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                              </div>
                            </div>
                            <div className="flex-1">
                              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                                {module.name}
                              </h3>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {module.description}
                              </p>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Active Module View */
          <div>
            <button
              onClick={() => setActiveModule(null)}
              className="mb-4 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Modules
            </button>
            {ActiveComponent && <ActiveComponent />}
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketEducation;

