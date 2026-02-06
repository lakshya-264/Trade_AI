import React, { useState, useEffect } from 'react';
import StockCard from './StockCard';
import { api } from '../../services/api';

interface RealTimeStockCardProps {
  symbol: string;
  name: string;
  className?: string;
}

const RealTimeStockCard: React.FC<RealTimeStockCardProps> = ({ symbol, name, className }) => {
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchQuote = async () => {
      try {
        setLoading(true);
        const data = await api.getQuote(symbol);
        setQuote(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch price');
        console.error(`Failed to fetch quote for ${symbol}:`, err);
      } finally {
        setLoading(false);
      }
    };

    fetchQuote();
  }, [symbol]);

  if (loading) {
    return (
      <div className={`bg-card border border-border rounded-lg p-4 animate-pulse ${className}`}>
        <div className="h-6 bg-muted rounded mb-2"></div>
        <div className="h-4 bg-muted rounded mb-3"></div>
        <div className="h-8 bg-muted rounded mb-2"></div>
        <div className="h-4 bg-muted rounded"></div>
      </div>
    );
  }

  if (error || !quote) {
    return (
      <div className={`bg-card border border-border rounded-lg p-4 ${className}`}>
        <h3 className="font-semibold text-foreground text-lg">{symbol}</h3>
        <p className="text-sm text-muted-foreground">{name}</p>
        <div className="text-muted-foreground mt-2">
          Price unavailable
        </div>
      </div>
    );
  }

  return (
    <StockCard
      symbol={symbol}
      name={name}
      price={quote.last_price || 0}
      change={quote.change || 0}
      changePercent={quote.change_percent || 0}
      volume={quote.volume || 0}
      className={className}
    />
  );
};

export default RealTimeStockCard;
