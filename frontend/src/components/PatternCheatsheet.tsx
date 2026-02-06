import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';

interface PatternCheatsheetProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

// Simple mini-candle SVG
const MiniCandle: React.FC<{ up?: boolean; longUpper?: boolean; longLower?: boolean; smallBody?: boolean }>
  = ({ up = true, longUpper = false, longLower = false, smallBody = false }) => {
  const bodyColor = up ? '#10B981' : '#EF4444';
  const wickColor = up ? '#059669' : '#DC2626';
  const bodyHeight = smallBody ? 10 : 18;
  const bodyY = 16 - bodyHeight / 2;
  const upper = longUpper ? 14 : 6;
  const lower = longLower ? 14 : 6;
  return (
    <svg width="28" height="28" viewBox="0 0 28 28">
      <line x1="14" y1={bodyY - upper} x2="14" y2={bodyY + bodyHeight + lower} stroke={wickColor} strokeWidth="2" />
      <rect x="10" y={bodyY} width="8" height={bodyHeight} fill={bodyColor} stroke={wickColor} strokeWidth="1" rx="2" />
    </svg>
  );
};

const Section: React.FC<{ title: string; children: React.ReactNode }>
  = ({ title, children }) => (
  <div>
    <h4 className="text-sm font-semibold text-foreground mb-2">{title}</h4>
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {children}
    </div>
  </div>
);

const Item: React.FC<{ label: string; children: React.ReactNode }>
  = ({ label, children }) => (
  <div className="flex flex-col items-center gap-1 p-2 rounded border border-border">
    <div>{children}</div>
    <div className="text-xs text-muted-foreground text-center leading-tight">{label}</div>
  </div>
);

const PatternCheatsheet: React.FC<PatternCheatsheetProps> = ({ isOpen, onClose, className }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className={cn("relative bg-card border border-border rounded-lg shadow-xl max-w-3xl w-full mx-4 p-4 sm:p-6 space-y-5", className)}>
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-2 rounded hover:bg-muted/50 text-muted-foreground"
          aria-label="Close"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>

        <h3 className="text-lg font-semibold text-foreground">Candlestick Pattern Cheatsheet</h3>

        <Section title="Bullish Reversal Patterns">
          <Item label="Hammer"><MiniCandle up longLower smallBody /></Item>
          <Item label="Inverted Hammer"><MiniCandle up longUpper smallBody /></Item>
          <Item label="Bullish Engulfing"><MiniCandle up /></Item>
          <Item label="Dark Cloud Cover"><MiniCandle up /></Item>
        </Section>

        <Section title="Bearish Reversal Patterns">
          <Item label="Hanging Man"><MiniCandle up={false} longLower smallBody /></Item>
          <Item label="Shooting Star"><MiniCandle up={false} longUpper smallBody /></Item>
          <Item label="Bearish Engulfing"><MiniCandle up={false} /></Item>
          <Item label="Evening Star"><MiniCandle up={false} /></Item>
        </Section>

        <Section title="Continuation Patterns">
          <Item label="Rising Three Methods"><MiniCandle up /></Item>
          <Item label="Falling Three Methods"><MiniCandle up={false} /></Item>
          <Item label="Bullish Harami"><MiniCandle up /></Item>
          <Item label="Tasuki Gap (Bullish)"><MiniCandle up /></Item>
        </Section>

        <Section title="Indecision / Neutral Patterns">
          <Item label="Doji">
            <svg width="28" height="28" viewBox="0 0 28 28">
              <line x1="14" y1="4" x2="14" y2="24" stroke="#6B7280" strokeWidth="2" />
              <line x1="8" y1="14" x2="20" y2="14" stroke="#6B7280" strokeWidth="2" />
            </svg>
          </Item>
          <Item label="Long-Legged Doji">
            <svg width="28" height="28" viewBox="0 0 28 28">
              <line x1="14" y1="2" x2="14" y2="26" stroke="#A855F7" strokeWidth="2" />
              <line x1="8" y1="14" x2="20" y2="14" stroke="#A855F7" strokeWidth="2" />
            </svg>
          </Item>
          <Item label="Spinning Top"><MiniCandle up smallBody longUpper longLower /></Item>
          <Item label="Rickshaw Man">
            <svg width="28" height="28" viewBox="0 0 28 28">
              <line x1="14" y1="2" x2="14" y2="26" stroke="#22C55E" strokeWidth="2" />
              <rect x="12.5" y="12" width="3" height="4" fill="#22C55E" />
            </svg>
          </Item>
        </Section>
      </div>
    </div>
  );
};

export default PatternCheatsheet;


