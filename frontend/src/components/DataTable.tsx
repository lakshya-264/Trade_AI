import React, { useState, useMemo } from 'react';
import { useVirtualScroll } from '../hooks/useVirtualScroll';
import { useDebounce } from '../hooks/useDebounce';
import ResponsiveCard from './ResponsiveCard';

interface Column<T> {
  key: keyof T;
  title: string;
  width?: number;
  render?: (value: any, row: T) => React.ReactNode;
  sortable?: boolean;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  height?: number;
  searchable?: boolean;
  searchFields?: (keyof T)[];
  sortable?: boolean;
  pagination?: boolean;
  pageSize?: number;
  className?: string;
}

const DataTable = <T extends Record<string, any>>({
  data,
  columns,
  height = 400,
  searchable = false,
  searchFields = [],
  sortable = true,
  pagination = false,
  pageSize = 50,
  className = ''
}: DataTableProps<T>) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof T | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);

  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Filter data based on search term
  const filteredData = useMemo(() => {
    if (!searchable || !debouncedSearchTerm) return data;

    return data.filter(row => {
      const searchFieldsToUse = searchFields.length > 0 ? searchFields : columns.map(col => col.key);
      
      return searchFieldsToUse.some(field => {
        const value = row[field];
        return value?.toString().toLowerCase().includes(debouncedSearchTerm.toLowerCase());
      });
    });
  }, [data, debouncedSearchTerm, searchable, searchFields, columns]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortable || !sortField) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortField, sortDirection, sortable]);

  // Paginate data
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;

    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return sortedData.slice(startIndex, endIndex);
  }, [sortedData, currentPage, pageSize, pagination]);

  // Virtual scrolling
  const virtualScroll = useVirtualScroll(paginatedData, {
    itemHeight: 50,
    containerHeight: height,
    overscan: 5
  });

  const handleSort = (field: keyof T) => {
    if (!sortable) return;

    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const totalPages = Math.ceil(filteredData.length / pageSize);

  return (
    <ResponsiveCard className={className}>
      {/* Search */}
      {searchable && (
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <div
          className="relative"
          style={{ height: `${height}px`, overflowY: 'auto' }}
        >
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                {columns.map((column, index) => (
                  <th
                    key={index}
                    className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                      column.sortable !== false && sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                    }`}
                    style={{ width: column.width }}
                    onClick={() => column.sortable !== false && handleSort(column.key)}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{column.title}</span>
                      {sortField === column.key && (
                        <span className="text-blue-500">
                          {sortDirection === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {virtualScroll.visibleItems.map((row, index) => (
                <tr
                  key={virtualScroll.startIndex + index}
                  className="hover:bg-gray-50"
                  style={{
                    position: 'absolute',
                    top: virtualScroll.offsetY + index * 50,
                    left: 0,
                    right: 0,
                    height: '50px'
                  }}
                >
                  {columns.map((column, colIndex) => (
                    <td
                      key={colIndex}
                      className="px-4 py-3 text-sm text-gray-900"
                      style={{ width: column.width }}
                    >
                      {column.render 
                        ? column.render((row as any)[column.key], row)
                        : (row as any)[column.key]
                      }
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {pagination && totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-700">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, filteredData.length)} of {filteredData.length} results
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </ResponsiveCard>
  );
};

export default DataTable;
