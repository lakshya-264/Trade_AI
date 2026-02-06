import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';

interface TechnicalIndicatorsGuideProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

const Section: React.FC<{ title: string; children: React.ReactNode }>
  = ({ title, children }) => (
  <div className="space-y-3">
    <h4 className="text-base font-semibold text-foreground">{title}</h4>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {children}
    </div>
  </div>
);

const Card: React.FC<{ title: string; formula?: React.ReactNode; children?: React.ReactNode }>
  = ({ title, formula, children }) => (
  <div className="rounded-lg border border-border p-4 bg-card/60">
    <div className="text-sm font-medium text-foreground mb-2">{title}</div>
    {formula && (
      <pre className="text-xs bg-muted/50 text-muted-foreground rounded p-3 overflow-x-auto mb-2 whitespace-pre-wrap">
{`${formula}`}
      </pre>
    )}
    {children && (
      <div className="text-xs text-muted-foreground leading-relaxed">{children}</div>
    )}
  </div>
);

const TechnicalIndicatorsGuide: React.FC<TechnicalIndicatorsGuideProps> = ({ isOpen, onClose, className }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className={cn(
        'relative bg-card border border-border rounded-lg shadow-xl w-[95vw] max-w-6xl max-h-[90vh] overflow-y-auto p-6 space-y-6',
        className
      )}>
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-2 rounded hover:bg-muted/50 text-muted-foreground"
          aria-label="Close"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>

        <div>
          <h3 className="text-xl font-semibold text-foreground">Complete Technical Indicators Guide</h3>
          <p className="text-sm text-muted-foreground">Dark Mode Edition – Optimized for intraday trading and market analysis</p>
        </div>

        <Section title="Trend Indicators">
          <Card title="Moving Average (MA)" formula={`MA = (Sum of Closing Prices over n periods) / n`}>
            Types: SMA, EMA, WMA. Common periods: 20, 50, 200. Usage: Golden Cross (50MA {'>'} 200MA), Death Cross (50MA {'<'} 200MA).
          </Card>
          <Card title="Exponential Moving Average (EMA)" formula={`EMA = (Price × K) + (Previous EMA × (1 - K))\nWhere K = 2 ÷ (n + 1)`}>
            Intraday: 9EMA, 21EMA for short-term trends. Responds faster than SMA.
          </Card>
          <Card title="MACD" formula={`MACD = 12EMA - 26EMA\nSignal = 9EMA of MACD\nHistogram = MACD - Signal`}>
            Bullish: MACD crosses above Signal. Bearish: MACD crosses below Signal. Divergences can precede reversals.
          </Card>
          <Card title="Average Directional Index (ADX)" formula={`ADX = 14-period SMA of DX\nDX = 100 × (|+DI - -DI| ÷ (+DI + -DI))`}>
            Range 0–100. Strong trend: ADX {'>'} 25. Direction via +DI / -DI.
          </Card>
          <Card title="Parabolic SAR" formula={`SAR = Prev SAR + AF × (EP - Prev SAR)`}>
            Dots below price (bullish), above price (bearish). Acts as stop-and-reverse trail.
          </Card>
        </Section>

        <Section title="Momentum Indicators">
          <Card title="RSI" formula={`RSI = 100 - [100 ÷ (1 + RS)]\nRS = Avg Gain ÷ Avg Loss`}>
            Overbought {'>'} 70, Oversold {'<'} 30. Divergences are powerful reversal signals.
          </Card>
          <Card title="Stochastic Oscillator" formula={`%K = 100 × [(Close - Lowest Low) ÷ (Highest High - Lowest Low)]\n%D = 3-period MA of %K`}>
            Slow Stochastic is more reliable. Overbought {'>'}80, Oversold {'<'}20. Use %K/%D crossovers.
          </Card>
          <Card title="CCI" formula={`CCI = (Typical Price - SMA(TP)) ÷ (0.015 × Mean Dev)\nTP = (High + Low + Close) ÷ 3`}>
            Neutral -100..+100. {'>'}+100 overbought; {'<'}-100 oversold. Extremes indicate strong trend.
          </Card>
          <Card title="ROC" formula={`ROC = [(Current Price ÷ Price n periods ago) - 1] × 100`}>
            Momentum positive/negative; zero-line crossovers flag trend changes.
          </Card>
        </Section>

        <Section title="Volatility Indicators">
          <Card title="Bollinger Bands" formula={`Mid = 20SMA\nUpper = Mid + 2×StdDev\nLower = Mid - 2×StdDev`}>
            Squeeze indicates potential breakout; extremes favor mean reversion.
          </Card>
          <Card title="ATR" formula={`True Range = max(High-Low, |High-Prev Close|, |Low-Prev Close|)\nATR = 14-SMA(True Range)`}>
            Higher ATR = higher volatility. Stops typically 1.5–2×ATR.
          </Card>
          <Card title="Donchian Channels" formula={`Upper = Highest High(n)\nLower = Lowest Low(n)\nMiddle = (Upper+Lower)/2`}>
            Breakout system; width reflects volatility. Turtle strategy used 20/55.
          </Card>
        </Section>

        <Section title="Volume Indicators">
          <Card title="On-Balance Volume (OBV)" formula={`OBV_t = OBV_{t-1} ± Volume_t (± depends on close up/down)`}>
            Confirms trend; divergences warn of weakness.
          </Card>
          <Card title="Chaikin Money Flow (CMF)" formula={`MF Mult = [(Close - Low) - (High - Close)] ÷ (High - Low)\nMF Vol = MF Mult × Volume\nCMF = Sum(MFV, n) ÷ Sum(Vol, n)`}>
            Range -1..+1; {'>'}+0.05 bullish, {'<'}-0.05 bearish.
          </Card>
          <Card title="VWAP" formula={`VWAP = Cum(Price × Volume) ÷ Cum(Volume)`}>
            Intraday benchmark; dynamic support/resistance.
          </Card>
        </Section>

        <Section title="Hybrid Indicators">
          <Card title="Ichimoku Cloud" formula={`Tenkan=(9H+9L)/2\nKijun=(26H+26L)/2\nSpan A=(Tenkan+Kijun)/2 (shift+26)\nSpan B=(52H+52L)/2 (shift+26)\nChikou=Close (shift-26)`}>
            All-in-one system; price vs cloud defines bias; Kumo twists hint changes.
          </Card>
          <Card title="Keltner Channels" formula={`Mid = 20EMA\nUpper = 20EMA + 2×ATR\nLower = 20EMA - 2×ATR`}>
            ATR-based bands; smoother than Bollinger.
          </Card>
          <Card title="Supertrend" formula={`Upper = (H+L)/2 + Mult×ATR\nLower = (H+L)/2 - Mult×ATR`}>
            Trend-following with trailing stop; common: ATR(10), Mult=3.
          </Card>
        </Section>

        <Section title="Custom & Derived">
          <Card title="Pivot Points" formula={`PP=(H+L+C)/3\nR1=(2×PP)-L\nS1=(2×PP)-H\nR2=PP+(H-L)\nS2=PP-(H-L)`}>
            Intraday levels for S/R and range trading; moves beyond R2/S2 show strength.
          </Card>
          <Card title="Fibonacci Retracement" formula={`Key: 23.6%, 38.2%, 50%, 61.8%, 78.6%` }>
            Use for pullbacks within trends; extensions 127.2%, 161.8% for targets.
          </Card>
          <Card title="Heikin-Ashi" formula={`HA Close=(O+H+L+C)/4\nHA Open=(Prev HA O + Prev HA C)/2\nHA High=max(H,HA O,HA C)\nHA Low=min(L,HA O,HA C)`}>
            Smooths noise; easier trend identification; no gaps.
          </Card>
        </Section>

        <Section title="Quick Reference & Intraday Playbook">
          <Card title="Trend Identification">
            MA/EMA crossovers; MACD momentum + trend; ADX{'>'}25 strong; Parabolic SAR flip.
          </Card>
          <Card title="Momentum & OB/OS">
            RSI 70/30, Stochastic 80/20, CCI ±100, ROC zero-line.
          </Card>
          <Card title="Volatility & Risk">
            BB squeeze + breakouts; ATR-based stops; Donchian breakout levels.
          </Card>
          <Card title="Volume Confirmation">
            OBV confirmation; CMF money flow; VWAP as the key intraday level.
          </Card>
          <Card title="Intraday Setups">
            Opening range with VWAP + pivots; Trend-follow with 9/21EMA & ATR stops; Mean reversion via BB extremes + reversal candles; Breakouts with BB squeeze + Donchian.
          </Card>
        </Section>
      </div>
    </div>
  );
};

export default TechnicalIndicatorsGuide;


