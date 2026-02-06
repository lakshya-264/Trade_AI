export const formatINR = (value?: number, fractionDigits: number = 2): string => {
  if (typeof value !== 'number' || isNaN(value)) return '₹0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits,
  }).format(value);
};

export const formatINRCompact = (value?: number, fractionDigits: number = 1): string => {
  if (typeof value !== 'number' || isNaN(value)) return '₹0.0';
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  const fmt = (n: number, suffix: string) => `${sign}₹${n.toFixed(fractionDigits)}${suffix}`;

  if (abs >= 1_00_00_000) {
    // Crores
    return fmt(abs / 1_00_00_000, 'Cr');
  }
  if (abs >= 1_00_000) {
    // Lakhs
    return fmt(abs / 1_00_000, 'L');
  }
  if (abs >= 1_000) {
    // Thousands
    return fmt(abs / 1_000, 'K');
  }
  return formatINR(value, Math.min(2, fractionDigits));
};

// Alias for compatibility
export const formatCurrency = formatINR;

export const formatPercentage = (value?: number, fractionDigits: number = 2): string => {
  if (typeof value !== 'number' || isNaN(value)) return '0.00%';
  return `${value >= 0 ? '+' : ''}${value.toFixed(fractionDigits)}%`;
};


