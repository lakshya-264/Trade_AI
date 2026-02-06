/**
 * IPO Markets Education Module
 * Comprehensive IPO education with calculators
 */

import React, { useState, useEffect } from 'react';
import { httpClient } from '../../config/api';
import { CalculatorIcon, BookOpenIcon, ChartBarIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

interface LessonSection {
  title: string;
  content: string;
  key_points?: string[];
}

interface IPOLesson {
  title: string;
  sections?: LessonSection[];
}

interface IPOJargon {
  term?: string;
  definition?: string;
  importance?: string;
}

interface IPOValuationMetrics {
  market_cap?: number;
  pe_ratio?: number;
  ps_ratio?: number;
  ev_ebitda?: number;
  [key: string]: number | undefined;
}

interface ListingGainResult {
  gain_per_share?: number;
  total_gain?: number;
  gain_percentage?: number;
}

interface IPOLessonsResponse {
  lessons?: Record<string, IPOLesson>;
}

interface IPOJargonsResponse {
  jargons?: Record<string, IPOJargon>;
}

interface IPOValuationResponse {
  metrics?: IPOValuationMetrics;
}

const IPOMarketsModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'lessons' | 'jargons' | 'analyze' | 'calculators'>('lessons');
  const [lessons, setLessons] = useState<Record<string, IPOLesson> | null>(null);
  const [jargons, setJargons] = useState<Record<string, IPOJargon> | null>(null);
  const [loading, setLoading] = useState(false);

  // Calculator states
  const [ipoPrice, setIpoPrice] = useState('');
  const [totalShares, setTotalShares] = useState('');
  const [revenue, setRevenue] = useState('');
  const [netProfit, setNetProfit] = useState('');
  const [debt, setDebt] = useState('');
  const [cash, setCash] = useState('');
  const [valuationMetrics, setValuationMetrics] = useState<IPOValuationMetrics | null>(null);

  // Listing gain calculator
  const [listingIpoPrice, setListingIpoPrice] = useState('');
  const [listingPrice, setListingPrice] = useState('');
  const [sharesAllotted, setSharesAllotted] = useState('');
  const [listingGain, setListingGain] = useState<ListingGainResult | null>(null);

  useEffect(() => {
    if (activeTab === 'lessons') {
      loadLessons();
    } else if (activeTab === 'jargons') {
      loadJargons();
    }
  }, [activeTab]);

  const loadLessons = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get<IPOLessonsResponse>('/api/market-education/ipo/lessons');
      if (response.success) {
        setLessons(response.data?.lessons ?? null);
      }
    } catch (error: any) {
      toast.error('Failed to load IPO lessons');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadJargons = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get<IPOJargonsResponse>('/api/market-education/ipo/jargons');
      if (response.success) {
        setJargons(response.data?.jargons ?? null);
      }
    } catch (error: any) {
      toast.error('Failed to load IPO jargons');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateValuationMetrics = async () => {
    try {
      if (!ipoPrice || !totalShares) {
        toast.error('Please enter IPO price and total shares');
        return;
      }

      setLoading(true);
      const response = await httpClient.post<IPOValuationResponse>('/api/market-education/ipo/calculate-metrics', {
        ipo_price: parseFloat(ipoPrice),
        total_shares: parseFloat(totalShares),
        revenue: revenue ? parseFloat(revenue) : undefined,
        net_profit: netProfit ? parseFloat(netProfit) : undefined,
        debt: debt ? parseFloat(debt) : undefined,
        cash: cash ? parseFloat(cash) : undefined
      });

      if (response.success) {
        let metrics: IPOValuationMetrics | null = null;
        const metricsPayload = response.data;

        if (metricsPayload?.metrics) {
          metrics = metricsPayload.metrics;
        } else if (
          metricsPayload &&
          typeof metricsPayload === 'object' &&
          ('market_cap' in metricsPayload ||
            'pe_ratio' in metricsPayload ||
            'ps_ratio' in metricsPayload ||
            'ev_ebitda' in metricsPayload)
        ) {
          metrics = metricsPayload as IPOValuationMetrics;
        }

        if (metrics) {
          setValuationMetrics(metrics);
        } else {
          setValuationMetrics(null);
        }
        toast.success('Valuation metrics calculated');
      }
    } catch (error: any) {
      toast.error('Failed to calculate metrics');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateListingGain = async () => {
    try {
      if (!listingIpoPrice || !listingPrice || !sharesAllotted) {
        toast.error('Please enter all fields');
        return;
      }

      setLoading(true);
      const response = await fetch(
        `/api/market-education/ipo/calculate-listing-gain?ipo_price=${listingIpoPrice}&listing_price=${listingPrice}&shares=${sharesAllotted}`
      );
      const data = await response.json();

      if (data.success) {
        setListingGain(data.results || data.data);
        toast.success('Listing gain calculated');
      }
    } catch (error: any) {
      toast.error('Failed to calculate listing gain');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <ChartBarIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">IPO Markets</h2>
            <p className="text-gray-600 dark:text-gray-400">Complete guide to IPO investing</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-1 px-6">
          {[
            { id: 'lessons', label: 'Lessons', icon: BookOpenIcon },
            { id: 'jargons', label: 'Jargons', icon: DocumentTextIcon },
            { id: 'calculators', label: 'Calculators', icon: CalculatorIcon }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'lessons' && (
          <div className="space-y-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
              </div>
            ) : lessons ? (
              Object.entries(lessons).map(([key, lesson]: [string, any]) => (
                <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                    {lesson.title}
                  </h3>
                  {lesson.sections?.map((section: any, idx: number) => (
                    <div key={idx} className="mb-6">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                        {section.title}
                      </h4>
                      <p className="text-gray-700 dark:text-gray-300 mb-3">
                        {section.content}
                      </p>
                      {section.key_points && (
                        <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                          {section.key_points.map((point: string, i: number) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-gray-500">No lessons available</div>
            )}
          </div>
        )}

        {activeTab === 'jargons' && (
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
              </div>
            ) : jargons ? (
              Object.entries(jargons).map(([key, jargon]: [string, any]) => (
                <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-2">
                    {jargon.term || key}
                  </h3>
                  <p className="text-gray-700 dark:text-gray-300 mb-2">
                    {jargon.definition}
                  </p>
                  {jargon.importance && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      <strong>Importance:</strong> {jargon.importance}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-gray-500">No jargons available</div>
            )}
          </div>
        )}

        {activeTab === 'calculators' && (
          <div className="space-y-8">
            {/* Valuation Calculator */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                IPO Valuation Calculator
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    IPO Price (₹)
                  </label>
                  <input
                    type="number"
                    value={ipoPrice}
                    onChange={(e) => setIpoPrice(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="950"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Total Shares (Cr)
                  </label>
                  <input
                    type="number"
                    value={totalShares}
                    onChange={(e) => setTotalShares(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Revenue (₹ Cr)
                  </label>
                  <input
                    type="number"
                    value={revenue}
                    onChange={(e) => setRevenue(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="1000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Net Profit (₹ Cr)
                  </label>
                  <input
                    type="number"
                    value={netProfit}
                    onChange={(e) => setNetProfit(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Debt (₹ Cr)
                  </label>
                  <input
                    type="number"
                    value={debt}
                    onChange={(e) => setDebt(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Cash (₹ Cr)
                  </label>
                  <input
                    type="number"
                    value={cash}
                    onChange={(e) => setCash(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="200"
                  />
                </div>
              </div>
              <button
                onClick={calculateValuationMetrics}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
              >
                Calculate Metrics
              </button>

              {valuationMetrics && (
                <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Results:</h4>
                  <div className="grid grid-cols-2 gap-4">
                    {valuationMetrics.market_cap && (
                      <div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">Market Cap:</span>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">
                          ₹{valuationMetrics.market_cap.toLocaleString('en-IN')} Cr
                        </p>
                      </div>
                    )}
                    {valuationMetrics.pe_ratio && (
                      <div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">PE Ratio:</span>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">
                          {valuationMetrics.pe_ratio.toFixed(2)}
                        </p>
                      </div>
                    )}
                    {valuationMetrics.ps_ratio && (
                      <div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">PS Ratio:</span>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">
                          {valuationMetrics.ps_ratio.toFixed(2)}
                        </p>
                      </div>
                    )}
                    {valuationMetrics.ev_ebitda && (
                      <div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">EV/EBITDA:</span>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">
                          {valuationMetrics.ev_ebitda.toFixed(2)}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Listing Gain Calculator */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Listing Gain Calculator
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    IPO Price (₹)
                  </label>
                  <input
                    type="number"
                    value={listingIpoPrice}
                    onChange={(e) => setListingIpoPrice(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Listing Price (₹)
                  </label>
                  <input
                    type="number"
                    value={listingPrice}
                    onChange={(e) => setListingPrice(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="120"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Shares Allotted
                  </label>
                  <input
                    type="number"
                    value={sharesAllotted}
                    onChange={(e) => setSharesAllotted(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="15"
                  />
                </div>
              </div>
              <button
                onClick={calculateListingGain}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
              >
                Calculate Gain
              </button>

              {listingGain && (
                <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Results:</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Gain per Share:</span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        ₹{listingGain.gain_per_share?.toFixed(2) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Total Gain:</span>
                      <span className="font-semibold text-green-600 dark:text-green-400">
                        ₹{listingGain.total_gain?.toFixed(2) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Gain %:</span>
                      <span className="font-semibold text-green-600 dark:text-green-400">
                        {listingGain.gain_percentage?.toFixed(2) || 'N/A'}%
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IPOMarketsModule;

