/**
 * Chart Data Utilities
 * Helper functions for processing chart data to ensure compatibility with lightweight-charts
 */

import { CandlestickData, LineData, HistogramData, Time, BusinessDay } from 'lightweight-charts';

/**
 * Deduplicate and sort chart data by time
 * Removes duplicate timestamps (keeps last occurrence) and ensures ascending order
 */
export function deduplicateAndSortCandlestickData(
  data: CandlestickData[],
  useBusinessDay: boolean = false
): CandlestickData[] {
  if (!data || data.length === 0) return [];

  // Convert to number for comparison if needed
  const getTimeValue = (item: CandlestickData): number => {
    if (useBusinessDay) {
      const time = item.time as BusinessDay;
      return new Date(time.year, time.month - 1, time.day).getTime();
    } else {
      return item.time as number;
    }
  };

  // Sort first - ensure proper numeric comparison
  const sortedData = [...data].sort((a, b) => {
    const timeA = getTimeValue(a);
    const timeB = getTimeValue(b);
    // Handle invalid times
    if (isNaN(timeA) || isNaN(timeB)) {
      console.warn('Invalid time value in sort:', a.time, b.time);
      return 0;
    }
    return timeA - timeB;
  });

  // Remove duplicates - keep last occurrence of each timestamp
  const uniqueData: CandlestickData[] = [];
  const seenTimes = new Set<number>();

  // Process in reverse to keep last occurrence
  for (let i = sortedData.length - 1; i >= 0; i--) {
    const item = sortedData[i];
    const timeValue = getTimeValue(item);

    // Skip invalid times
    if (isNaN(timeValue)) {
      console.warn('Skipping item with invalid time:', item);
      continue;
    }

    if (!seenTimes.has(timeValue)) {
      seenTimes.add(timeValue);
      uniqueData.unshift(item);
    }
  }

  // Final verification and ensure strict ascending order
  const finalData: CandlestickData[] = [];
  let prevTime: number | null = null;
  
  for (const item of uniqueData) {
    const timeValue = getTimeValue(item);
    
    // Skip invalid times
    if (isNaN(timeValue)) {
      console.warn('Skipping item with invalid time in final pass:', item);
      continue;
    }
    
    if (prevTime === null) {
      // First item
      finalData.push(item);
      prevTime = timeValue;
    } else if (timeValue > prevTime) {
      // Valid ascending order
      finalData.push(item);
      prevTime = timeValue;
    } else if (timeValue === prevTime) {
      // Exact duplicate - skip
      continue;
    } else {
      // Out of order - this should not happen after sorting, but log and skip
      console.error(`Data out of order detected: time=${timeValue}, prev time=${prevTime}. This should not happen after sorting!`);
      // Don't add this item to prevent assertion error
    }
  }

  // Final validation pass
  if (finalData.length > 1) {
    for (let i = 1; i < finalData.length; i++) {
      const prevTime = getTimeValue(finalData[i - 1]);
      const currTime = getTimeValue(finalData[i]);
      if (currTime <= prevTime) {
        console.error(`Final validation failed at index ${i}: time=${currTime}, prev time=${prevTime}`);
        // This is a critical error - re-sort the entire array
        return [...finalData].sort((a, b) => getTimeValue(a) - getTimeValue(b));
      }
    }
  }

  return finalData;
}

/**
 * Deduplicate and sort line data by time
 */
export function deduplicateAndSortLineData(
  data: LineData[],
  useBusinessDay: boolean = false
): LineData[] {
  if (!data || data.length === 0) return [];

  const getTimeValue = (item: LineData): number => {
    if (useBusinessDay) {
      const time = item.time as BusinessDay;
      return new Date(time.year, time.month - 1, time.day).getTime();
    } else {
      return item.time as number;
    }
  };

  const sortedData = [...data].sort((a, b) => getTimeValue(a) - getTimeValue(b));

  const uniqueData: LineData[] = [];
  const seenTimes = new Set<number>();

  for (let i = sortedData.length - 1; i >= 0; i--) {
    const item = sortedData[i];
    const timeValue = getTimeValue(item);

    if (!seenTimes.has(timeValue)) {
      seenTimes.add(timeValue);
      uniqueData.unshift(item);
    }
  }

  // Verify no duplicates remain
  const finalData: LineData[] = [];
  let prevTime: number | null = null;
  
  for (const item of uniqueData) {
    const timeValue = getTimeValue(item);
    if (prevTime === null || timeValue > prevTime) {
      finalData.push(item);
      prevTime = timeValue;
    } else if (timeValue === prevTime) {
      continue; // Skip duplicate
    }
  }

  return finalData;
}

/**
 * Deduplicate and sort histogram data by time
 */
export function deduplicateAndSortHistogramData(
  data: HistogramData[],
  useBusinessDay: boolean = false
): HistogramData[] {
  if (!data || data.length === 0) return [];

  const getTimeValue = (item: HistogramData): number => {
    if (useBusinessDay) {
      const time = item.time as BusinessDay;
      return new Date(time.year, time.month - 1, time.day).getTime();
    } else {
      return item.time as number;
    }
  };

  const sortedData = [...data].sort((a, b) => getTimeValue(a) - getTimeValue(b));

  const uniqueData: HistogramData[] = [];
  const seenTimes = new Set<number>();

  for (let i = sortedData.length - 1; i >= 0; i--) {
    const item = sortedData[i];
    const timeValue = getTimeValue(item);

    if (!seenTimes.has(timeValue)) {
      seenTimes.add(timeValue);
      uniqueData.unshift(item);
    }
  }

  // Verify no duplicates remain
  const finalData: HistogramData[] = [];
  let prevTime: number | null = null;
  
  for (const item of uniqueData) {
    const timeValue = getTimeValue(item);
    if (prevTime === null || timeValue > prevTime) {
      finalData.push(item);
      prevTime = timeValue;
    } else if (timeValue === prevTime) {
      continue; // Skip duplicate
    }
  }

  return finalData;
}

