import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { formatINR } from '../utils/currency';

interface QuoteLite {
  symbol: string;
  price?: number;
  change?: number;
  changePercent?: number;
}

const INDICES = [
  { id: 'NIFTY50', label: 'NIFTY 50' },
  { id: 'SENSEX', label: 'SENSEX' },
  { id: 'BANKNIFTY', label: 'BANKNIFTY' },
  { id: 'NIFTYIT', label: 'NIFTY IT' },
  { id: 'NIFTYNEXT50', label: 'NIFTY Next 50' },
  { id: 'NIFTY100', label: 'NIFTY 100' },
  { id: 'NIFTY500', label: 'NIFTY 500' },
  { id: 'NIFTYPHARMA', label: 'NIFTY Pharma' },
  { id: 'NIFTYAUTO', label: 'NIFTY Auto' },
  { id: 'NIFTYFMCG', label: 'NIFTY FMCG' },
  { id: 'NIFTYMETAL', label: 'NIFTY Metal' },
  { id: 'NIFTYREALTY', label: 'NIFTY Realty' },
  { id: 'NIFTYMEDIA', label: 'NIFTY Media' },
  { id: 'NIFTYPRIVATEBANK', label: 'NIFTY Private Bank' },
  { id: 'NIFTYPSUBANK', label: 'NIFTY PSU Bank' },
];

const concurrency = 4;

const IndexConstituentsView: React.FC = () => {
  const navigate = useNavigate();
  const [indexId, setIndexId] = useState<string>(() => localStorage.getItem('last_index') || 'NIFTY50');
  const [symbols, setSymbols] = useState<string[]>([]);
  const [quotes, setQuotes] = useState<Record<string, QuoteLite>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    localStorage.setItem('last_index', indexId);
  }, [indexId]);

  useEffect(() => {
    const run = async () => {
      try {
        setLoading(true);
        setError(null);
        setQuotes({});
        const res = await api.getIndexConstituents(indexId);
        const list = (res && (res as any).symbols) || [];
        setSymbols(list);

        // Use batch quotes for better performance
        const batchQuotes = await api.getBatchQuotes(list);
        const out: Record<string, QuoteLite> = {};
        
        batchQuotes.forEach(quote => {
          out[quote.symbol] = {
            symbol: quote.symbol,
            price: quote.last_price,
            change: quote.change,
            changePercent: quote.change_percent,
          };
        });
        
        // Fill in missing symbols with empty data
        list.forEach((sym: string) => {
          if (!out[sym]) {
            out[sym] = { symbol: sym };
          }
        });
        
        setQuotes(out);
      } catch (e: any) {
        setError(e?.message || 'Failed to load constituents');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [indexId]);

  const view = useMemo(() => {
    const f = filter.trim().toUpperCase();
    const base = f ? symbols.filter(s => s.includes(f)) : symbols;
    return base.map(s => quotes[s] || { symbol: s });
  }, [symbols, quotes, filter]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <select
          value={indexId}
          onChange={(e) => setIndexId(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        >
          {INDICES.map(i => (
            <option key={i.id} value={i.id}>{i.label}</option>
          ))}
        </select>
        <input
          placeholder="Filter symbols…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border rounded px-2 py-1 text-sm flex-1"
        />
      </div>

      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}

      <div className="h-96 overflow-auto border rounded">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-gray-50">
            <tr>
              <th className="text-left px-3 py-2">Symbol</th>
              <th className="text-right px-3 py-2">Price</th>
              <th className="text-right px-3 py-2">Change</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-3" colSpan={3}>Loading…</td></tr>
            ) : (
              view.map(row => (
                <tr key={row.symbol} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/symbol/${encodeURIComponent(row.symbol)}`)}>
                  <td className="px-3 py-2 font-medium">{row.symbol}</td>
                  <td className="px-3 py-2 text-right">{row.price ? formatINR(row.price) : '-'}</td>
                  <td className={"px-3 py-2 text-right " + (row.changePercent ? (row.changePercent >= 0 ? 'text-green-600' : 'text-red-600') : 'text-gray-500')}>
                    {row.changePercent !== undefined ? `${row.changePercent.toFixed(2)}%` : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default IndexConstituentsView;


