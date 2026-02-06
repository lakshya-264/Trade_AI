/**
 * Index Stocks Database
 * Contains all stocks organized by their respective indexes
 */

export interface IndexStock {
  symbol: string;
  name: string;
  sector: string;
  marketCap?: string;
  weight?: number; // Index weight percentage
}

export interface IndexData {
  name: string;
  symbol: string;
  stocks: IndexStock[];
  description: string;
}

// NIFTY 50 Stocks
export const nifty50Stocks: IndexStock[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', sector: 'Energy', marketCap: '₹17.5L Cr', weight: 10.2 },
  { symbol: 'TCS', name: 'Tata Consultancy Services', sector: 'IT', marketCap: '₹13.2L Cr', weight: 7.8 },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', sector: 'Banking', marketCap: '₹11.8L Cr', weight: 7.1 },
  { symbol: 'INFY', name: 'Infosys', sector: 'IT', marketCap: '₹6.5L Cr', weight: 4.2 },
  { symbol: 'HINDUNILVR', name: 'Hindustan Unilever', sector: 'FMCG', marketCap: '₹5.9L Cr', weight: 3.8 },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', sector: 'Banking', marketCap: '₹7.2L Cr', weight: 4.5 },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Banking', marketCap: '₹3.8L Cr', weight: 2.3 },
  { symbol: 'ITC', name: 'ITC Limited', sector: 'FMCG', marketCap: '₹5.1L Cr', weight: 3.2 },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel', sector: 'Telecom', marketCap: '₹5.6L Cr', weight: 3.5 },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Banking', marketCap: '₹5.4L Cr', weight: 3.3 },
  { symbol: 'BAJFINANCE', name: 'Bajaj Finance', sector: 'Financial Services', marketCap: '₹4.1L Cr', weight: 2.5 },
  { symbol: 'ASIANPAINT', name: 'Asian Paints', sector: 'Consumer Durables', marketCap: '₹2.9L Cr', weight: 1.8 },
  { symbol: 'AXISBANK', name: 'Axis Bank', sector: 'Banking', marketCap: '₹3.2L Cr', weight: 2.0 },
  { symbol: 'MARUTI', name: 'Maruti Suzuki', sector: 'Automobile', marketCap: '₹3.5L Cr', weight: 2.2 },
  { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical', sector: 'Pharma', marketCap: '₹2.8L Cr', weight: 1.7 },
  { symbol: 'TITAN', name: 'Titan Company', sector: 'Consumer Durables', marketCap: '₹2.7L Cr', weight: 1.6 },
  { symbol: 'ULTRACEMCO', name: 'UltraTech Cement', sector: 'Cement', marketCap: '₹2.5L Cr', weight: 1.5 },
  { symbol: 'NESTLEIND', name: 'Nestle India', sector: 'FMCG', marketCap: '₹2.3L Cr', weight: 1.4 },
  { symbol: 'POWERGRID', name: 'Power Grid Corporation', sector: 'Power', marketCap: '₹2.2L Cr', weight: 1.3 },
  { symbol: 'NTPC', name: 'NTPC Limited', sector: 'Power', marketCap: '₹2.1L Cr', weight: 1.2 },
  { symbol: 'TECHM', name: 'Tech Mahindra', sector: 'IT', marketCap: '₹1.5L Cr', weight: 0.9 },
  { symbol: 'WIPRO', name: 'Wipro', sector: 'IT', marketCap: '₹2.3L Cr', weight: 1.4 },
  { symbol: 'HCLTECH', name: 'HCL Technologies', sector: 'IT', marketCap: '₹3.8L Cr', weight: 2.3 },
  { symbol: 'LT', name: 'Larsen & Toubro', sector: 'Engineering', marketCap: '₹4.5L Cr', weight: 2.7 },
  { symbol: 'BAJAJFINSV', name: 'Bajaj Finserv', sector: 'Financial Services', marketCap: '₹2.7L Cr', weight: 1.6 },
  { symbol: 'DRREDDY', name: 'Dr. Reddy\'s Laboratories', sector: 'Pharma', marketCap: '₹1.0L Cr', weight: 0.6 },
  { symbol: 'TATAMOTORS', name: 'Tata Motors', sector: 'Automobile', marketCap: '₹3.2L Cr', weight: 1.9 },
  { symbol: 'BRITANNIA', name: 'Britannia Industries', sector: 'FMCG', marketCap: '₹1.3L Cr', weight: 0.8 },
  { symbol: 'EICHERMOT', name: 'Eicher Motors', sector: 'Automobile', marketCap: '₹1.2L Cr', weight: 0.7 },
  { symbol: 'SHREECEM', name: 'Shree Cement', sector: 'Cement', marketCap: '₹0.9L Cr', weight: 0.5 },
  { symbol: 'JSWSTEEL', name: 'JSW Steel', sector: 'Steel', marketCap: '₹2.0L Cr', weight: 1.2 },
  { symbol: 'TATASTEEL', name: 'Tata Steel', sector: 'Steel', marketCap: '₹1.4L Cr', weight: 0.8 },
  { symbol: 'INDUSINDBK', name: 'IndusInd Bank', sector: 'Banking', marketCap: '₹1.1L Cr', weight: 0.7 },
  { symbol: 'COALINDIA', name: 'Coal India', sector: 'Mining', marketCap: '₹2.7L Cr', weight: 1.6 },
  { symbol: 'GRASIM', name: 'Grasim Industries', sector: 'Cement', marketCap: '₹1.3L Cr', weight: 0.8 },
  { symbol: 'CIPLA', name: 'Cipla', sector: 'Pharma', marketCap: '₹1.1L Cr', weight: 0.7 },
  { symbol: 'ONGC', name: 'Oil & Natural Gas Corporation', sector: 'Oil & Gas', marketCap: '₹3.1L Cr', weight: 1.9 },
  { symbol: 'TATACONSUM', name: 'Tata Consumer Products', sector: 'FMCG', marketCap: '₹0.9L Cr', weight: 0.5 },
  { symbol: 'APOLLOHOSP', name: 'Apollo Hospitals', sector: 'Healthcare', marketCap: '₹0.8L Cr', weight: 0.5 },
  { symbol: 'ADANIPORTS', name: 'Adani Ports', sector: 'Infrastructure', marketCap: '₹2.3L Cr', weight: 1.4 },
  { symbol: 'BPCL', name: 'Bharat Petroleum', sector: 'Oil & Gas', marketCap: '₹1.0L Cr', weight: 0.6 },
  { symbol: 'HEROMOTOCO', name: 'Hero MotoCorp', sector: 'Automobile', marketCap: '₹0.9L Cr', weight: 0.5 },
  { symbol: 'DIVISLAB', name: 'Divi\'s Laboratories', sector: 'Pharma', marketCap: '₹0.9L Cr', weight: 0.5 },
  { symbol: 'UPL', name: 'UPL Limited', sector: 'Chemicals', marketCap: '₹0.4L Cr', weight: 0.2 },
  { symbol: 'BAJAJ-AUTO', name: 'Bajaj Auto', sector: 'Automobile', marketCap: '₹2.5L Cr', weight: 1.5 },
  { symbol: 'TATAPOWER', name: 'Tata Power', sector: 'Power', marketCap: '₹1.1L Cr', weight: 0.7 },
  { symbol: 'ADANIENT', name: 'Adani Enterprises', sector: 'Diversified', marketCap: '₹3.0L Cr', weight: 1.8 },
  { symbol: 'SBILIFE', name: 'SBI Life Insurance', sector: 'Insurance', marketCap: '₹1.4L Cr', weight: 0.8 },
  { symbol: 'HINDALCO', name: 'Hindalco Industries', sector: 'Metals', marketCap: '₹1.2L Cr', weight: 0.7 },
  { symbol: 'HDFCLIFE', name: 'HDFC Life Insurance', sector: 'Insurance', marketCap: '₹1.5L Cr', weight: 0.9 },
  // Additional stocks
  { symbol: 'NMDC', name: 'NMDC Limited', sector: 'Steel', marketCap: '₹0.8L Cr', weight: 0.5 },
  { symbol: 'INFIBEAM', name: 'Infibeam Avenues', sector: 'IT', marketCap: '₹0.3L Cr', weight: 0.2 },
  { symbol: 'INDIANREN', name: 'Indian Renewable Energy', sector: 'Power', marketCap: '₹0.2L Cr', weight: 0.1 },
  { symbol: 'TANLA', name: 'Tanla Platforms', sector: 'IT', marketCap: '₹0.4L Cr', weight: 0.2 },
  { symbol: 'BIRLASOFT', name: 'Birlasoft', sector: 'IT', marketCap: '₹0.5L Cr', weight: 0.3 },
  { symbol: 'SUZLON', name: 'Suzlon Energy', sector: 'Power', marketCap: '₹0.6L Cr', weight: 0.4 },
  { symbol: 'SAKSOFT', name: 'Saksoft', sector: 'IT', marketCap: '₹0.1L Cr', weight: 0.1 },
  { symbol: 'GAIL', name: 'GAIL India', sector: 'Oil & Gas', marketCap: '₹1.1L Cr', weight: 0.7 },
  { symbol: 'ADANIGREEN', name: 'Adani Green Energy', sector: 'Power', marketCap: '₹2.5L Cr', weight: 1.5 },
  { symbol: 'NHPC', name: 'NHPC Limited', sector: 'Power', marketCap: '₹0.9L Cr', weight: 0.5 },
  { symbol: 'COCHINSHIP', name: 'Cochin Shipyard', sector: 'Infrastructure', marketCap: '₹0.4L Cr', weight: 0.2 },
  { symbol: 'IRB', name: 'IRB Infrastructure Developers', sector: 'Infrastructure', marketCap: '₹0.3L Cr', weight: 0.2 },
  { symbol: 'BAJAJHLDNG', name: 'Bajaj Housing Finance', sector: 'Financial Services', marketCap: '₹0.2L Cr', weight: 0.1 },
  { symbol: 'HGIEL', name: 'Hindustan Green Energy', sector: 'Power', marketCap: '₹0.1L Cr', weight: 0.1 },
];

// SENSEX 30 Stocks (Top 30 from NIFTY 50)
export const sensex30Stocks: IndexStock[] = nifty50Stocks.slice(0, 30);

// BANK NIFTY Stocks
export const bankNiftyStocks: IndexStock[] = [
  { symbol: 'HDFCBANK', name: 'HDFC Bank', sector: 'Banking', marketCap: '₹11.8L Cr', weight: 25.5 },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', sector: 'Banking', marketCap: '₹7.2L Cr', weight: 18.2 },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Banking', marketCap: '₹5.4L Cr', weight: 12.8 },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Banking', marketCap: '₹3.8L Cr', weight: 9.5 },
  { symbol: 'AXISBANK', name: 'Axis Bank', sector: 'Banking', marketCap: '₹3.2L Cr', weight: 8.1 },
  { symbol: 'INDUSINDBK', name: 'IndusInd Bank', sector: 'Banking', marketCap: '₹1.1L Cr', weight: 2.8 },
  { symbol: 'FEDERALBNK', name: 'Federal Bank', sector: 'Banking', marketCap: '₹0.6L Cr', weight: 1.5 },
  { symbol: 'PNB', name: 'Punjab National Bank', sector: 'Banking', marketCap: '₹0.8L Cr', weight: 2.0 },
  { symbol: 'BANDHANBNK', name: 'Bandhan Bank', sector: 'Banking', marketCap: '₹0.4L Cr', weight: 1.0 },
  { symbol: 'IDFCFIRSTB', name: 'IDFC First Bank', sector: 'Banking', marketCap: '₹0.5L Cr', weight: 1.3 },
  { symbol: 'AUBANK', name: 'AU Small Finance Bank', sector: 'Banking', marketCap: '₹0.3L Cr', weight: 0.8 },
  { symbol: 'RBLBANK', name: 'RBL Bank', sector: 'Banking', marketCap: '₹0.2L Cr', weight: 0.5 },
];

// NIFTY MIDCAP 50 Stocks
export const midcapNiftyStocks: IndexStock[] = [
  { symbol: 'ADANIPOWER', name: 'Adani Power', sector: 'Power', marketCap: '₹1.8L Cr', weight: 3.2 },
  { symbol: 'VEDL', name: 'Vedanta Limited', sector: 'Metals', marketCap: '₹1.5L Cr', weight: 2.7 },
  { symbol: 'JINDALSTEL', name: 'Jindal Steel & Power', sector: 'Steel', marketCap: '₹1.2L Cr', weight: 2.1 },
  { symbol: 'MOTHERSON', name: 'Motherson Sumi', sector: 'Automobile', marketCap: '₹1.0L Cr', weight: 1.8 },
  { symbol: 'PAGEIND', name: 'Page Industries', sector: 'Textiles', marketCap: '₹0.9L Cr', weight: 1.6 },
  { symbol: 'ALKEM', name: 'Alkem Laboratories', sector: 'Pharma', marketCap: '₹0.8L Cr', weight: 1.4 },
  { symbol: 'TORNTPHARM', name: 'Torrent Pharmaceuticals', sector: 'Pharma', marketCap: '₹0.7L Cr', weight: 1.2 },
  { symbol: 'LALPATHLAB', name: 'Dr. Lal PathLabs', sector: 'Healthcare', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'DABUR', name: 'Dabur India', sector: 'FMCG', marketCap: '₹0.9L Cr', weight: 1.6 },
  { symbol: 'MARICO', name: 'Marico Limited', sector: 'FMCG', marketCap: '₹0.7L Cr', weight: 1.2 },
  { symbol: 'GODREJCP', name: 'Godrej Consumer Products', sector: 'FMCG', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'COLPAL', name: 'Colgate-Palmolive', sector: 'FMCG', marketCap: '₹0.5L Cr', weight: 0.9 },
  { symbol: 'HAVELLS', name: 'Havells India', sector: 'Consumer Durables', marketCap: '₹0.8L Cr', weight: 1.4 },
  { symbol: 'VOLTAS', name: 'Voltas Limited', sector: 'Consumer Durables', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'WHIRLPOOL', name: 'Whirlpool India', sector: 'Consumer Durables', marketCap: '₹0.4L Cr', weight: 0.7 },
  { symbol: 'ESCORTS', name: 'Escorts Kubota', sector: 'Automobile', marketCap: '₹0.5L Cr', weight: 0.9 },
  { symbol: 'ASHOKLEY', name: 'Ashok Leyland', sector: 'Automobile', marketCap: '₹0.7L Cr', weight: 1.2 },
  { symbol: 'M&M', name: 'Mahindra & Mahindra', sector: 'Automobile', marketCap: '₹1.8L Cr', weight: 3.2 },
  { symbol: 'TVSMOTOR', name: 'TVS Motor Company', sector: 'Automobile', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'BHARATFORG', name: 'Bharat Forge', sector: 'Automobile', marketCap: '₹0.5L Cr', weight: 0.9 },
  { symbol: 'RAMCOCEM', name: 'Ramco Cements', sector: 'Cement', marketCap: '₹0.4L Cr', weight: 0.7 },
  { symbol: 'ACC', name: 'ACC Limited', sector: 'Cement', marketCap: '₹0.5L Cr', weight: 0.9 },
  { symbol: 'AMBUJACEM', name: 'Ambuja Cements', sector: 'Cement', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'DALBHARAT', name: 'Dalmia Bharat', sector: 'Cement', marketCap: '₹0.4L Cr', weight: 0.7 },
  { symbol: 'JKCEMENT', name: 'JK Cement', sector: 'Cement', marketCap: '₹0.3L Cr', weight: 0.5 },
  { symbol: 'GODREJPROP', name: 'Godrej Properties', sector: 'Real Estate', marketCap: '₹0.5L Cr', weight: 0.9 },
  { symbol: 'DLF', name: 'DLF Limited', sector: 'Real Estate', marketCap: '₹0.7L Cr', weight: 1.2 },
  { symbol: 'OBEROIRLTY', name: 'Oberoi Realty', sector: 'Real Estate', marketCap: '₹0.4L Cr', weight: 0.7 },
  { symbol: 'PRESTIGE', name: 'Prestige Estates', sector: 'Real Estate', marketCap: '₹0.3L Cr', weight: 0.5 },
  { symbol: 'SOBHA', name: 'Sobha Limited', sector: 'Real Estate', marketCap: '₹0.2L Cr', weight: 0.4 },
  { symbol: 'GODREJIND', name: 'Godrej Industries', sector: 'Diversified', marketCap: '₹0.4L Cr', weight: 0.7 },
  { symbol: 'ITC', name: 'ITC Limited', sector: 'FMCG', marketCap: '₹5.1L Cr', weight: 9.1 },
  { symbol: 'NESTLEIND', name: 'Nestle India', sector: 'FMCG', marketCap: '₹2.3L Cr', weight: 4.1 },
  { symbol: 'BRITANNIA', name: 'Britannia Industries', sector: 'FMCG', marketCap: '₹1.3L Cr', weight: 2.3 },
  { symbol: 'TATACONSUM', name: 'Tata Consumer Products', sector: 'FMCG', marketCap: '₹0.9L Cr', weight: 1.6 },
  { symbol: 'DABUR', name: 'Dabur India', sector: 'FMCG', marketCap: '₹0.9L Cr', weight: 1.6 },
  { symbol: 'MARICO', name: 'Marico Limited', sector: 'FMCG', marketCap: '₹0.7L Cr', weight: 1.2 },
  { symbol: 'GODREJCP', name: 'Godrej Consumer Products', sector: 'FMCG', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'COLPAL', name: 'Colgate-Palmolive', sector: 'FMCG', marketCap: '₹0.5L Cr', weight: 0.9 },
  { symbol: 'EMAMILTD', name: 'Emami Limited', sector: 'FMCG', marketCap: '₹0.3L Cr', weight: 0.5 },
  { symbol: 'JUBLFOOD', name: 'Jubilant FoodWorks', sector: 'FMCG', marketCap: '₹0.4L Cr', weight: 0.7 },
  // Additional stocks
  { symbol: 'NMDC', name: 'NMDC Limited', sector: 'Steel', marketCap: '₹0.8L Cr', weight: 1.4 },
  { symbol: 'INFIBEAM', name: 'Infibeam Avenues', sector: 'IT', marketCap: '₹0.3L Cr', weight: 0.5 },
  { symbol: 'INDIANREN', name: 'Indian Renewable Energy', sector: 'Power', marketCap: '₹0.2L Cr', weight: 0.4 },
  { symbol: 'TANLA', name: 'Tanla Platforms', sector: 'IT', marketCap: '₹0.4L Cr', weight: 0.7 },
  { symbol: 'BIRLASOFT', name: 'Birlasoft', sector: 'IT', marketCap: '₹0.5L Cr', weight: 0.9 },
  { symbol: 'SUZLON', name: 'Suzlon Energy', sector: 'Power', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'SAKSOFT', name: 'Saksoft', sector: 'IT', marketCap: '₹0.1L Cr', weight: 0.2 },
  { symbol: 'GAIL', name: 'GAIL India', sector: 'Oil & Gas', marketCap: '₹1.1L Cr', weight: 2.0 },
  { symbol: 'ADANIGREEN', name: 'Adani Green Energy', sector: 'Power', marketCap: '₹2.5L Cr', weight: 4.5 },
  { symbol: 'NHPC', name: 'NHPC Limited', sector: 'Power', marketCap: '₹0.9L Cr', weight: 1.6 },
  { symbol: 'COCHINSHIP', name: 'Cochin Shipyard', sector: 'Infrastructure', marketCap: '₹0.4L Cr', weight: 0.7 },
  { symbol: 'IRB', name: 'IRB Infrastructure Developers', sector: 'Infrastructure', marketCap: '₹0.3L Cr', weight: 0.5 },
  { symbol: 'BAJAJHLDNG', name: 'Bajaj Housing Finance', sector: 'Financial Services', marketCap: '₹0.2L Cr', weight: 0.4 },
  { symbol: 'HGIEL', name: 'Hindustan Green Energy', sector: 'Power', marketCap: '₹0.1L Cr', weight: 0.2 },
  { symbol: 'BSE', name: 'BSE Limited', sector: 'Financial Services', marketCap: '₹0.5L Cr', weight: 0.9 },
];

// FIN NIFTY Stocks (Financial Services)
export const finNiftyStocks: IndexStock[] = [
  { symbol: 'HDFCBANK', name: 'HDFC Bank', sector: 'Banking', marketCap: '₹11.8L Cr', weight: 18.5 },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', sector: 'Banking', marketCap: '₹7.2L Cr', weight: 11.2 },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Banking', marketCap: '₹5.4L Cr', weight: 8.4 },
  { symbol: 'BAJFINANCE', name: 'Bajaj Finance', sector: 'Financial Services', marketCap: '₹4.1L Cr', weight: 6.4 },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Banking', marketCap: '₹3.8L Cr', weight: 5.9 },
  { symbol: 'AXISBANK', name: 'Axis Bank', sector: 'Banking', marketCap: '₹3.2L Cr', weight: 5.0 },
  { symbol: 'BAJAJFINSV', name: 'Bajaj Finserv', sector: 'Financial Services', marketCap: '₹2.7L Cr', weight: 4.2 },
  { symbol: 'HDFCLIFE', name: 'HDFC Life Insurance', sector: 'Insurance', marketCap: '₹1.5L Cr', weight: 2.3 },
  { symbol: 'SBILIFE', name: 'SBI Life Insurance', sector: 'Insurance', marketCap: '₹1.4L Cr', weight: 2.2 },
  { symbol: 'ICICIPRULI', name: 'ICICI Prudential Life', sector: 'Insurance', marketCap: '₹1.2L Cr', weight: 1.9 },
  { symbol: 'ICICIGI', name: 'ICICI Lombard', sector: 'Insurance', marketCap: '₹0.9L Cr', weight: 1.4 },
  { symbol: 'HDFCAMC', name: 'HDFC Asset Management', sector: 'Financial Services', marketCap: '₹0.8L Cr', weight: 1.2 },
  { symbol: 'MUTHOOTFIN', name: 'Muthoot Finance', sector: 'Financial Services', marketCap: '₹0.7L Cr', weight: 1.1 },
  { symbol: 'CHOLAFIN', name: 'Cholamandalam Finance', sector: 'Financial Services', marketCap: '₹0.6L Cr', weight: 0.9 },
  { symbol: 'SRTRANSFIN', name: 'Shriram Transport Finance', sector: 'Financial Services', marketCap: '₹0.5L Cr', weight: 0.8 },
  { symbol: 'M&MFIN', name: 'Mahindra & Mahindra Financial', sector: 'Financial Services', marketCap: '₹0.4L Cr', weight: 0.6 },
  { symbol: 'PFC', name: 'Power Finance Corporation', sector: 'Financial Services', marketCap: '₹0.6L Cr', weight: 0.9 },
  { symbol: 'RECLTD', name: 'REC Limited', sector: 'Financial Services', marketCap: '₹0.5L Cr', weight: 0.8 },
  { symbol: 'IRFC', name: 'Indian Railway Finance', sector: 'Financial Services', marketCap: '₹0.4L Cr', weight: 0.6 },
  { symbol: 'LICI', name: 'Life Insurance Corporation', sector: 'Insurance', marketCap: '₹5.2L Cr', weight: 8.1 },
  { symbol: 'BAJAJHLDNG', name: 'Bajaj Housing Finance', sector: 'Financial Services', marketCap: '₹0.2L Cr', weight: 0.3 },
  { symbol: 'BSE', name: 'BSE Limited', sector: 'Financial Services', marketCap: '₹0.5L Cr', weight: 0.8 },
];

// BANKEX Stocks (Banking Index - BSE)
export const bankexStocks: IndexStock[] = [
  { symbol: 'HDFCBANK', name: 'HDFC Bank', sector: 'Banking', marketCap: '₹11.8L Cr', weight: 22.5 },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', sector: 'Banking', marketCap: '₹7.2L Cr', weight: 13.8 },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Banking', marketCap: '₹5.4L Cr', weight: 10.3 },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Banking', marketCap: '₹3.8L Cr', weight: 7.3 },
  { symbol: 'AXISBANK', name: 'Axis Bank', sector: 'Banking', marketCap: '₹3.2L Cr', weight: 6.1 },
  { symbol: 'INDUSINDBK', name: 'IndusInd Bank', sector: 'Banking', marketCap: '₹1.1L Cr', weight: 2.1 },
  { symbol: 'FEDERALBNK', name: 'Federal Bank', sector: 'Banking', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'PNB', name: 'Punjab National Bank', sector: 'Banking', marketCap: '₹0.8L Cr', weight: 1.5 },
  { symbol: 'BANDHANBNK', name: 'Bandhan Bank', sector: 'Banking', marketCap: '₹0.4L Cr', weight: 0.8 },
  { symbol: 'IDFCFIRSTB', name: 'IDFC First Bank', sector: 'Banking', marketCap: '₹0.5L Cr', weight: 1.0 },
  { symbol: 'AUBANK', name: 'AU Small Finance Bank', sector: 'Banking', marketCap: '₹0.3L Cr', weight: 0.6 },
  { symbol: 'RBLBANK', name: 'RBL Bank', sector: 'Banking', marketCap: '₹0.2L Cr', weight: 0.4 },
  { symbol: 'YESBANK', name: 'Yes Bank', sector: 'Banking', marketCap: '₹0.5L Cr', weight: 1.0 },
  { symbol: 'UNIONBANK', name: 'Union Bank of India', sector: 'Banking', marketCap: '₹0.7L Cr', weight: 1.3 },
  { symbol: 'CANBK', name: 'Canara Bank', sector: 'Banking', marketCap: '₹0.6L Cr', weight: 1.1 },
  { symbol: 'BANKBARODA', name: 'Bank of Baroda', sector: 'Banking', marketCap: '₹0.9L Cr', weight: 1.7 },
  { symbol: 'IOB', name: 'Indian Overseas Bank', sector: 'Banking', marketCap: '₹0.3L Cr', weight: 0.6 },
  { symbol: 'CENTRALBK', name: 'Central Bank of India', sector: 'Banking', marketCap: '₹0.2L Cr', weight: 0.4 },
  { symbol: 'UCOBANK', name: 'UCO Bank', sector: 'Banking', marketCap: '₹0.2L Cr', weight: 0.4 },
  { symbol: 'INDIANB', name: 'Indian Bank', sector: 'Banking', marketCap: '₹0.4L Cr', weight: 0.8 },
];

// All Indexes Data
export const indexData: Record<string, IndexData> = {
  'NIFTY': {
    name: 'NIFTY 50',
    symbol: 'NIFTY_50',
    stocks: nifty50Stocks,
    description: 'Top 50 companies by market capitalization on NSE'
  },
  'SENSEX': {
    name: 'SENSEX',
    symbol: 'SENSEX',
    stocks: sensex30Stocks,
    description: 'Top 30 companies by market capitalization on BSE'
  },
  'BANKNIFTY': {
    name: 'BANK NIFTY',
    symbol: 'NIFTYBANK',
    stocks: bankNiftyStocks,
    description: 'Top banking stocks on NSE'
  },
  'MIDCPNIFTY': {
    name: 'NIFTY MIDCAP 50',
    symbol: 'NIFTYMIDCAP50',
    stocks: midcapNiftyStocks,
    description: 'Top 50 mid-cap companies on NSE'
  },
  'FINNIFTY': {
    name: 'FIN NIFTY',
    symbol: 'NIFTYFIN',
    stocks: finNiftyStocks,
    description: 'Top financial services companies on NSE'
  },
  'BANKEX': {
    name: 'BANKEX',
    symbol: 'BANKEX',
    stocks: bankexStocks,
    description: 'Top banking stocks on BSE'
  }
};

// Get all unique sectors across all indexes
export const getAllSectors = (): string[] => {
  const sectors = new Set<string>();
  Object.values(indexData).forEach(index => {
    index.stocks.forEach(stock => {
      sectors.add(stock.sector);
    });
  });
  return Array.from(sectors).sort();
};

// Get stocks by sector
export const getStocksBySector = (sector: string): IndexStock[] => {
  const stocks: IndexStock[] = [];
  Object.values(indexData).forEach(index => {
    index.stocks.forEach(stock => {
      if (stock.sector === sector) {
        stocks.push(stock);
      }
    });
  });
  return stocks;
};

