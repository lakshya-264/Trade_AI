import React, { useEffect, useMemo, useState } from 'react';
import { Search, RefreshCw, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { httpClient } from '../config/api';

interface LatestResultsRow {
  symbol?: string | null;
  company_name?: string | null;
  company_url?: string | null;
  result_date?: string | null;
  quarter?: string | null;
}

interface LatestResultsApiData {
  rows?: LatestResultsRow[];
  source?: string;
}

const NseResults: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const [rows, setRows] = useState<LatestResultsRow[]>([]);
  const [totalRows, setTotalRows] = useState<number>(0);

  const fetchRows = async () => {
    setLoading(true);
    setError(null);

    try {
      const resp = await httpClient.get<LatestResultsApiData>(`/api/screener/latest-results?ttl_minutes=30`);

      if (!resp?.success) {
        throw new Error(resp?.error || resp?.message || 'Failed to fetch NSE results');
      }

      const data = resp?.data || {};
      const results = Array.isArray(data.rows) ? data.rows : [];

      setRows(results);
      setTotalRows(results.length);
    } catch (e: any) {
      setError(e?.message || 'Failed to fetch NSE results');
      setRows([]);
      setTotalRows(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const today = useMemo(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  }, []);

  const filteredRows = useMemo(() => {
    const q = query.trim().toUpperCase();
    if (!q) return rows;
    return rows.filter(r => {
      const sym = (r.symbol || '').toUpperCase();
      const name = (r.company_name || '').toUpperCase();
      return sym.includes(q) || name.includes(q);
    });
  }, [rows, query]);

  const sortedRows = useMemo(() => {
    const copy = [...filteredRows];
    copy.sort((a, b) => {
      const ad = a.result_date ? new Date(a.result_date).getTime() : -Infinity;
      const bd = b.result_date ? new Date(b.result_date).getTime() : -Infinity;
      return bd - ad;
    });
    return copy;
  }, [filteredRows]);

  const groupToday = useMemo(() => {
    return sortedRows.filter(r => {
      if (!r.result_date) return false;
      const d = new Date(r.result_date);
      d.setHours(0, 0, 0, 0);
      return d.getTime() === today.getTime();
    });
  }, [sortedRows, today]);

  const groupUpcoming = useMemo(() => {
    return sortedRows.filter(r => {
      if (!r.result_date) return false;
      const d = new Date(r.result_date);
      d.setHours(0, 0, 0, 0);
      return d.getTime() > today.getTime();
    });
  }, [sortedRows, today]);

  const groupPast = useMemo(() => {
    return sortedRows.filter(r => {
      if (!r.result_date) return false;
      const d = new Date(r.result_date);
      d.setHours(0, 0, 0, 0);
      return d.getTime() < today.getTime();
    });
  }, [sortedRows, today]);

  const totalPages = useMemo(() => {
    const maxLen = Math.max(groupToday.length, groupUpcoming.length, groupPast.length);
    return Math.max(1, Math.ceil(maxLen / pageSize));
  }, [groupToday.length, groupUpcoming.length, groupPast.length, pageSize]);

  const pagedStart = (page - 1) * pageSize;
  const todaysResults = useMemo(() => groupToday.slice(pagedStart, pagedStart + pageSize), [groupToday, pagedStart, pageSize]);
  const upcomingResults = useMemo(() => groupUpcoming.slice(pagedStart, pagedStart + pageSize), [groupUpcoming, pagedStart, pageSize]);
  const pastResults = useMemo(() => groupPast.slice(pagedStart, pagedStart + pageSize), [groupPast, pagedStart, pageSize]);

  const onSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  const renderTable = (data: LatestResultsRow[]) => {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 font-semibold text-gray-700">Symbol</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-700">Company</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-700">Result Date</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-700">Quarter</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.map((r) => (
                <tr key={`${r.symbol || r.company_name || 'row'}-${r.result_date || 'na'}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold text-gray-900">{r.symbol || '-'}</td>
                  <td className="px-4 py-3 text-gray-700">{r.company_name || '-'}</td>
                  <td className="px-4 py-3 text-gray-700">{r.result_date ? new Date(r.result_date).toLocaleDateString() : '-'}</td>
                  <td className="px-4 py-3 text-gray-700">{r.quarter || '-'}</td>
                </tr>
              ))}
              {!data.length && (
                <tr>
                  <td className="px-4 py-6 text-gray-500" colSpan={4}>No results</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const canPrev = page > 1;
  const canNext = page < totalPages;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">NSE Results</h1>
          <div className="text-sm text-gray-500">Rows: {totalRows.toLocaleString()}</div>
        </div>
        <button
          onClick={fetchRows}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm space-y-4">
        <form onSubmit={onSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search symbol or company"
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={pageSize}
              onChange={(e) => {
                setPage(1);
                setPageSize(Number(e.target.value));
              }}
              className="px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
            </select>
            <button
              type="submit"
              className="px-4 py-2 rounded-md bg-gray-900 text-white hover:bg-black"
              disabled={loading}
            >
              Search
            </button>
          </div>
        </form>

        {error && (
          <div className="flex items-start gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md p-3">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <div>{error}</div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">Page {page} of {totalPages}</div>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={!canPrev || loading}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-md border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-60"
          >
            <ChevronLeft className="w-4 h-4" />
            Prev
          </button>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={!canNext || loading}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-md border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-60"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-gray-900">Today</h2>
          {renderTable(todaysResults)}
        </div>

        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-gray-900">Upcoming</h2>
          {renderTable(upcomingResults)}
        </div>

        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-gray-900">Past</h2>
          {renderTable(pastResults)}
        </div>
      </div>
    </div>
  );
};

export default NseResults;
