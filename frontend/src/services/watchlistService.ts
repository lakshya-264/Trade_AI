/**
 * Watchlist Service
 * Manages watchlist operations (add, remove, get)
 */

const WATCHLIST_STORAGE_KEY = 'trading_watchlist';

export const watchlistService = {
  /**
   * Get all symbols in watchlist
   */
  getWatchlist(): string[] {
    try {
      const saved = localStorage.getItem(WATCHLIST_STORAGE_KEY);
      return saved ? JSON.parse(saved) : ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK'];
    } catch (error) {
      console.error('Error loading watchlist:', error);
      return [];
    }
  },

  /**
   * Add symbol to watchlist
   */
  addSymbol(symbol: string): boolean {
    try {
      const watchlist = this.getWatchlist();
      if (!watchlist.includes(symbol)) {
        watchlist.push(symbol);
        localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      return false;
    }
  },

  /**
   * Remove symbol from watchlist
   */
  removeSymbol(symbol: string): boolean {
    try {
      const watchlist = this.getWatchlist();
      const filtered = watchlist.filter(s => s !== symbol);
      localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(filtered));
      return true;
    } catch (error) {
      console.error('Error removing from watchlist:', error);
      return false;
    }
  },

  /**
   * Check if symbol is in watchlist
   */
  isInWatchlist(symbol: string): boolean {
    const watchlist = this.getWatchlist();
    return watchlist.includes(symbol);
  }
};

