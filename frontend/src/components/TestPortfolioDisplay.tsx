import React, { useEffect, useState } from 'react';
import { httpClient } from '../config/api';

interface PortfolioData {
  holdings: Record<string, any>;
  total_value: number;
  holding_count: number;
  trades: any[];
  trade_count: number;
}

const TestPortfolioDisplay = () => {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('🔍 Fetching portfolio data...');
        const response = await httpClient.get('/api/v1/direct-portfolio');
        console.log('📊 Full response:', response);
        
        if (response.success) {
          console.log('✅ Portfolio data:', response.data);
          setData(response.data as PortfolioData);
        } else {
          console.error('❌ API returned success=false');
          setError('API failed');
        }
      } catch (error) {
        console.error('❌ Fetch error:', error);
        setError((error as Error).message);
      }
    };
    
    fetchData();
  }, []);
  
  if (error) return (
    <div style={{color: 'red', padding: '20px', border: '1px solid red', margin: '20px'}}>
      <h3>❌ Error: {error}</h3>
      <p>Check browser console for more details</p>
    </div>
  );
  
  if (!data) return (
    <div style={{padding: '20px', margin: '20px'}}>
      <h3>🔄 Loading portfolio data...</h3>
    </div>
  );
  
  return (
    <div style={{padding: '20px', border: '2px solid #007bff', margin: '20px', borderRadius: '8px'}}>
      <h2>🎯 TEST PORTFOLIO DISPLAY</h2>
      
      <div style={{marginBottom: '20px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px'}}>
        <p><strong>📊 Total Value:</strong> ₹{data.total_value?.toLocaleString()}</p>
        <p><strong>📈 Holding Count:</strong> {data.holding_count}</p>
        <p><strong>💼 Trade Count:</strong> {data.trade_count}</p>
      </div>
      
      <h3>📈 Holdings:</h3>
      {data.holdings && Object.entries(data.holdings).map(([symbol, holding]: [string, any]) => (
        <div key={symbol} style={{margin: '10px 0', padding: '15px', border: '1px solid #ddd', borderRadius: '4px', backgroundColor: '#fff'}}>
          <strong style={{color: '#007bff'}}>{symbol}</strong><br />
          <span style={{color: '#666'}}>Quantity:</span> {holding.quantity}<br />
          <span style={{color: '#666'}}>Avg Price:</span> ₹{holding.avg_price}<br />
          <span style={{color: '#666'}}>Current Price:</span> ₹{holding.current_price}<br />
          <span style={{color: '#666'}}>Total Value:</span> ₹{holding.total_value?.toLocaleString()}
          {holding.unrealized_pnl !== undefined && (
            <>
              <br />
              <span style={{color: holding.unrealized_pnl >= 0 ? 'green' : 'red'}}>
                P&L: ₹{holding.unrealized_pnl?.toLocaleString()} ({holding.unrealized_pnl_percent?.toFixed(2)}%)
              </span>
            </>
          )}
        </div>
      ))}
      
      <h3>💼 Recent Trades:</h3>
      {data.trades && data.trades.map((trade: any, index: number) => (
        <div key={index} style={{margin: '5px 0', padding: '8px', fontSize: '12px', border: '1px solid #eee', borderRadius: '4px'}}>
          <strong>{trade.symbol}</strong>: {trade.signal_type} {trade.quantity} @ ₹{trade.entry_price} 
          <span style={{color: trade.status === 'ACTIVE' ? 'green' : 'orange'}}> ({trade.status})</span>
        </div>
      ))}
      
      <div style={{marginTop: '20px', padding: '10px', backgroundColor: '#e7f3ff', borderRadius: '4px'}}>
        <small>
          💡 <strong>Debug Info:</strong> Check browser console (F12) for detailed API response logs
        </small>
      </div>
    </div>
  );
};

export default TestPortfolioDisplay;
