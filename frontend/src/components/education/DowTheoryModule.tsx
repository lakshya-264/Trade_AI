/**
 * Dow Theory Education Module
 * Dow Theory principles and pattern detection
 */

import React, { useState } from 'react';
import { ChartBarIcon, LightBulbIcon } from '@heroicons/react/24/outline';

const DowTheoryModule: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string>('principles');

  const dowTheoryContent = {
    principles: {
      title: "Six Basic Principles of Dow Theory",
      items: [
        {
          title: "1. The Averages Discount Everything",
          description: "Stock prices reflect all available information",
          details: "Technical analysis focuses on price action, not news. All known information is already priced in."
        },
        {
          title: "2. Three Types of Trends",
          description: "Primary (major), Secondary (corrections), Minor (daily fluctuations)",
          details: "Primary trends last 1-3 years, secondary trends are 3 weeks to 3 months, and minor trends are daily fluctuations."
        },
        {
          title: "3. Trend Phases",
          description: "Three phases in both bull and bear markets",
          details: "Bull markets: Accumulation → Public Participation → Distribution. Bear markets: Distribution → Public Participation → Accumulation."
        },
        {
          title: "4. Averages Must Confirm",
          description: "Industrial and Transportation averages must confirm each other",
          details: "Both averages must make new highs/lows together. Non-confirmation is a warning sign."
        },
        {
          title: "5. Volume Confirms Trend",
          description: "Volume should increase in direction of trend",
          details: "In bull markets, volume increases on up days. In bear markets, volume increases on down days."
        },
        {
          title: "6. Trend Remains Until Reversal",
          description: "Trend continues until clear reversal signals",
          details: "Reversal signals include failure to make new high/low, break of previous swing point, and volume confirmation."
        }
      ]
    },
    tradingRanges: {
      title: "Trading Ranges and Flags",
      description: "Price consolidation patterns within trends",
      content: "Flags are brief consolidations after strong moves. They slope against the main trend, volume decreases during the flag, and breakout occurs in the direction of the main trend."
    },
    riskReward: {
      title: "Risk-Reward Ratio",
      description: "Measure potential profit vs potential loss",
      content: "Should be at least 2:1 (risk ₹1 to make ₹2). Calculate as Reward / Risk."
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <ChartBarIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Dow Theory</h2>
            <p className="text-gray-600 dark:text-gray-400">Principles and pattern detection</p>
          </div>
        </div>
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-1 px-6">
          {['principles', 'ranges', 'risk'].map((section) => (
            <button
              key={section}
              onClick={() => setActiveSection(section)}
              className={`px-4 py-3 font-medium text-sm border-b-2 ${
                activeSection === section
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400'
              }`}
            >
              {section === 'principles' ? 'Principles' : section === 'ranges' ? 'Trading Ranges' : 'Risk-Reward'}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {activeSection === 'principles' && (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              {dowTheoryContent.principles.title}
            </h3>
            {dowTheoryContent.principles.items.map((principle, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="flex items-start gap-3 mb-3">
                  <LightBulbIcon className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {principle.title}
                    </h4>
                    <p className="text-gray-700 dark:text-gray-300 mb-2 font-medium">
                      {principle.description}
                    </p>
                    <p className="text-gray-600 dark:text-gray-400">
                      {principle.details}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeSection === 'ranges' && (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              {dowTheoryContent.tradingRanges.title}
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              {dowTheoryContent.tradingRanges.description}
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              {dowTheoryContent.tradingRanges.content}
            </p>
          </div>
        )}

        {activeSection === 'risk' && (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              {dowTheoryContent.riskReward.title}
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              {dowTheoryContent.riskReward.description}
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              {dowTheoryContent.riskReward.content}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DowTheoryModule;
