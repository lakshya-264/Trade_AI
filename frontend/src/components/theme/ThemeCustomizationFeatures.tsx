import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import {
  SwatchIcon, SunIcon, MoonIcon, ComputerDesktopIcon,
  EyeIcon, PaintBrushIcon, CogIcon,
  CheckIcon, XMarkIcon, ArrowPathIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';
import { toast } from 'react-hot-toast';

// Enhanced Theme Types
interface ColorScheme {
  id: string;
  name: string;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
    info: string;
  };
  isDark: boolean;
}

interface ThemeCustomization {
  colorScheme: string;
  fontSize: 'small' | 'medium' | 'large';
  borderRadius: 'none' | 'small' | 'medium' | 'large';
  spacing: 'compact' | 'comfortable' | 'spacious';
  animations: boolean;
  reducedMotion: boolean;
  highContrast: boolean;
  customColors?: {
    primary?: string;
    secondary?: string;
    accent?: string;
  };
}

interface ThemeContextType {
  currentTheme: ColorScheme;
  customization: ThemeCustomization;
  isDarkMode: boolean;
  toggleTheme: () => void;
  setColorScheme: (schemeId: string) => void;
  updateCustomization: (updates: Partial<ThemeCustomization>) => void;
  resetToDefault: () => void;
  previewTheme: (theme: Partial<ThemeCustomization>) => void;
  applyTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Predefined Color Schemes
const colorSchemes: ColorScheme[] = [
  {
    id: 'default-light',
    name: 'Light Professional',
    description: 'Clean and modern light theme',
    colors: {
      primary: '#3B82F6',
      secondary: '#64748B',
      accent: '#8B5CF6',
      background: '#FFFFFF',
      surface: '#F8FAFC',
      text: '#1E293B',
      textSecondary: '#64748B',
      border: '#E2E8F0',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#06B6D4'
    },
    isDark: false
  },
  {
    id: 'default-dark',
    name: 'Dark Professional',
    description: 'Professional dark theme for trading',
    colors: {
      primary: '#3B82F6',
      secondary: '#94A3B8',
      accent: '#A78BFA',
      background: '#0F172A',
      surface: '#1E293B',
      text: '#F8FAFC',
      textSecondary: '#94A3B8',
      border: '#334155',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#06B6D4'
    },
    isDark: true
  },
  {
    id: 'trading-light',
    name: 'Trading Light',
    description: 'Optimized for daytime trading',
    colors: {
      primary: '#059669',
      secondary: '#6B7280',
      accent: '#DC2626',
      background: '#FEFEFE',
      surface: '#F9FAFB',
      text: '#111827',
      textSecondary: '#6B7280',
      border: '#D1D5DB',
      success: '#059669',
      warning: '#D97706',
      error: '#DC2626',
      info: '#0284C7'
    },
    isDark: false
  },
  {
    id: 'trading-dark',
    name: 'Trading Dark',
    description: 'Optimized for night trading',
    colors: {
      primary: '#10B981',
      secondary: '#9CA3AF',
      accent: '#F87171',
      background: '#111827',
      surface: '#1F2937',
      text: '#F9FAFB',
      textSecondary: '#9CA3AF',
      border: '#374151',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#F87171',
      info: '#60A5FA'
    },
    isDark: true
  },
  {
    id: 'high-contrast',
    name: 'High Contrast',
    description: 'Maximum accessibility and readability',
    colors: {
      primary: '#0000FF',
      secondary: '#808080',
      accent: '#FF0000',
      background: '#FFFFFF',
      surface: '#F0F0F0',
      text: '#000000',
      textSecondary: '#333333',
      border: '#000000',
      success: '#008000',
      warning: '#FFA500',
      error: '#FF0000',
      info: '#0000FF'
    },
    isDark: false
  },
  {
    id: 'minimal',
    name: 'Minimal',
    description: 'Clean and distraction-free',
    colors: {
      primary: '#6366F1',
      secondary: '#8B5CF6',
      accent: '#EC4899',
      background: '#FAFAFA',
      surface: '#FFFFFF',
      text: '#18181B',
      textSecondary: '#71717A',
      border: '#E4E4E7',
      success: '#22C55E',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6'
    },
    isDark: false
  }
];

// Default Customization
const defaultCustomization: ThemeCustomization = {
  colorScheme: 'default-light',
  fontSize: 'medium',
  borderRadius: 'medium',
  spacing: 'comfortable',
  animations: true,
  reducedMotion: false,
  highContrast: false
};

// Theme Provider Component
export const EnhancedThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [customization, setCustomization] = useState<ThemeCustomization>(() => {
    const saved = localStorage.getItem('theme-customization');
    return saved ? { ...defaultCustomization, ...JSON.parse(saved) } : defaultCustomization;
  });

  const [previewMode, setPreviewMode] = useState(false);
  const [previewCustomization, setPreviewCustomization] = useState<ThemeCustomization | null>(null);

  const currentTheme = colorSchemes.find(scheme => scheme.id === customization.colorScheme) || colorSchemes[0];

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    const activeCustomization = previewMode && previewCustomization ? previewCustomization : customization;
    const activeTheme = colorSchemes.find(scheme => scheme.id === activeCustomization.colorScheme) || colorSchemes[0];

    // Apply color scheme
    Object.entries(activeTheme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });

    // Apply customization
    root.style.setProperty('--font-size-base', 
      activeCustomization.fontSize === 'small' ? '14px' :
      activeCustomization.fontSize === 'large' ? '18px' : '16px'
    );

    root.style.setProperty('--border-radius', 
      activeCustomization.borderRadius === 'none' ? '0px' :
      activeCustomization.borderRadius === 'small' ? '4px' :
      activeCustomization.borderRadius === 'large' ? '12px' : '8px'
    );

    root.style.setProperty('--spacing-scale', 
      activeCustomization.spacing === 'compact' ? '0.75' :
      activeCustomization.spacing === 'spacious' ? '1.25' : '1'
    );

    // Apply dark mode class
    if (activeTheme.isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Apply accessibility features
    if (activeCustomization.reducedMotion) {
      root.classList.add('reduce-motion');
    } else {
      root.classList.remove('reduce-motion');
    }

    if (activeCustomization.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Save to localStorage
    if (!previewMode) {
      localStorage.setItem('theme-customization', JSON.stringify(customization));
    }

  }, [customization, previewMode, previewCustomization]);

  const toggleTheme = () => {
    const newScheme = currentTheme.isDark ? 'default-light' : 'default-dark';
    setCustomization(prev => ({ ...prev, colorScheme: newScheme }));
  };

  const setColorScheme = (schemeId: string) => {
    setCustomization(prev => ({ ...prev, colorScheme: schemeId }));
  };

  const updateCustomization = (updates: Partial<ThemeCustomization>) => {
    setCustomization(prev => ({ ...prev, ...updates }));
  };

  const resetToDefault = () => {
    setCustomization(defaultCustomization);
    toast.success('Theme reset to default');
  };

  const previewTheme = (theme: Partial<ThemeCustomization>) => {
    setPreviewCustomization({ ...customization, ...theme });
    setPreviewMode(true);
  };

  const applyTheme = () => {
    if (previewCustomization) {
      setCustomization(previewCustomization);
      setPreviewMode(false);
      setPreviewCustomization(null);
      toast.success('Theme applied successfully');
    }
  };

  const value: ThemeContextType = {
    currentTheme,
    customization,
    isDarkMode: currentTheme.isDark,
    toggleTheme,
    setColorScheme,
    updateCustomization,
    resetToDefault,
    previewTheme,
    applyTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook to use theme context
export const useEnhancedTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useEnhancedTheme must be used within an EnhancedThemeProvider');
  }
  return context;
};

// Theme Customization Component
const ThemeCustomizationPanel: React.FC = () => {
  const {
    currentTheme,
    customization,
    setColorScheme,
    updateCustomization,
    resetToDefault,
    previewTheme,
    applyTheme
  } = useEnhancedTheme();

  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [previewSettings, setPreviewSettings] = useState<Partial<ThemeCustomization>>({});

  const handlePreview = (updates: Partial<ThemeCustomization>) => {
    setPreviewSettings(updates);
    previewTheme(updates);
    setIsPreviewMode(true);
  };

  const handleApply = () => {
    applyTheme();
    setIsPreviewMode(false);
    setPreviewSettings({});
  };

  const handleCancel = () => {
    setIsPreviewMode(false);
    setPreviewSettings({});
    // Reset preview by applying current customization
    previewTheme(customization);
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Theme Customization</h3>
        <div className="flex items-center space-x-2">
          {isPreviewMode && (
            <>
              <button
                onClick={handleApply}
                className="flex items-center px-3 py-1 bg-green-500 text-white rounded-md text-sm hover:bg-green-600"
              >
                <CheckIcon className="h-4 w-4 mr-1" />
                Apply
              </button>
              <button
                onClick={handleCancel}
                className="flex items-center px-3 py-1 bg-gray-500 text-white rounded-md text-sm hover:bg-gray-600"
              >
                <XMarkIcon className="h-4 w-4 mr-1" />
                Cancel
              </button>
            </>
          )}
          <button
            onClick={resetToDefault}
            className="flex items-center px-3 py-1 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md text-sm hover:bg-gray-300 dark:hover:bg-gray-500"
          >
            <ArrowPathIcon className="h-4 w-4 mr-1" />
            Reset
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Color Schemes */}
        <div>
          <h4 className="text-md font-medium mb-3">Color Schemes</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {colorSchemes.map((scheme) => (
              <div
                key={scheme.id}
                onClick={() => handlePreview({ colorScheme: scheme.id })}
                className={cn(
                  "p-3 border rounded-lg cursor-pointer transition-all",
                  customization.colorScheme === scheme.id
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                )}
              >
                <div className="flex items-center mb-2">
                  <div className="flex space-x-1 mr-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: scheme.colors.primary }}
                    />
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: scheme.colors.secondary }}
                    />
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: scheme.colors.accent }}
                    />
                  </div>
                  <h5 className="font-medium text-sm">{scheme.name}</h5>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">{scheme.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Typography */}
        <div>
          <h4 className="text-md font-medium mb-3">Typography</h4>
          <div className="grid grid-cols-3 gap-3">
            {(['small', 'medium', 'large'] as const).map((size) => (
              <button
                key={size}
                onClick={() => handlePreview({ fontSize: size })}
                className={cn(
                  "p-3 border rounded-lg text-center transition-all",
                  customization.fontSize === size
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                )}
              >
                <div className={cn(
                  "font-medium",
                  size === 'small' ? 'text-sm' : size === 'large' ? 'text-lg' : 'text-base'
                )}>
                  {size.charAt(0).toUpperCase() + size.slice(1)}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Border Radius */}
        <div>
          <h4 className="text-md font-medium mb-3">Border Radius</h4>
          <div className="grid grid-cols-4 gap-3">
            {(['none', 'small', 'medium', 'large'] as const).map((radius) => (
              <button
                key={radius}
                onClick={() => handlePreview({ borderRadius: radius })}
                className={cn(
                  "p-3 border text-center transition-all",
                  customization.borderRadius === radius
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600",
                  radius === 'none' ? 'rounded-none' :
                  radius === 'small' ? 'rounded-sm' :
                  radius === 'large' ? 'rounded-lg' : 'rounded-md'
                )}
              >
                <div className="text-sm font-medium">{radius.charAt(0).toUpperCase() + radius.slice(1)}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Spacing */}
        <div>
          <h4 className="text-md font-medium mb-3">Spacing</h4>
          <div className="grid grid-cols-3 gap-3">
            {(['compact', 'comfortable', 'spacious'] as const).map((spacing) => (
              <button
                key={spacing}
                onClick={() => handlePreview({ spacing })}
                className={cn(
                  "p-3 border rounded-lg text-center transition-all",
                  customization.spacing === spacing
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                )}
              >
                <div className="text-sm font-medium">{spacing.charAt(0).toUpperCase() + spacing.slice(1)}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Accessibility Options */}
        <div>
          <h4 className="text-md font-medium mb-3">Accessibility</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={customization.animations}
                onChange={(e) => handlePreview({ animations: e.target.checked })}
                className="mr-3"
              />
              <span className="text-sm">Enable animations</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={customization.reducedMotion}
                onChange={(e) => handlePreview({ reducedMotion: e.target.checked })}
                className="mr-3"
              />
              <span className="text-sm">Reduce motion</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={customization.highContrast}
                onChange={(e) => handlePreview({ highContrast: e.target.checked })}
                className="mr-3"
              />
              <span className="text-sm">High contrast mode</span>
            </label>
          </div>
        </div>

        {/* Custom Colors */}
        <div>
          <h4 className="text-md font-medium mb-3">Custom Colors</h4>
          <div className="grid grid-cols-3 gap-3">
            {(['primary', 'secondary', 'accent'] as const).map((color) => (
              <div key={color}>
                <label className="block text-sm font-medium mb-1 capitalize">{color}</label>
                <input
                  type="color"
                  value={currentTheme.colors[color]}
                  onChange={(e) => {
                    const customColors = { ...customization.customColors, [color]: e.target.value };
                    handlePreview({ customColors });
                  }}
                  className="w-full h-10 border border-gray-300 dark:border-gray-600 rounded-md"
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Theme Preview Component
const ThemePreview: React.FC = () => {
  const { currentTheme, customization } = useEnhancedTheme();

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Theme Preview</h3>
      
      <div className="space-y-4">
        {/* Sample Components */}
        <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h4 className="font-semibold mb-2">Sample Components</h4>
          <div className="space-y-2">
            <button className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">
              Primary Button
            </button>
            <button className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-500">
              Secondary Button
            </button>
          </div>
        </div>

        {/* Color Palette */}
        <div>
          <h4 className="font-semibold mb-2">Color Palette</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(currentTheme.colors).map(([name, color]) => (
              <div key={name} className="text-center">
                <div
                  className="w-full h-8 rounded border"
                  style={{ backgroundColor: color }}
                />
                <div className="text-xs mt-1 capitalize">{name}</div>
                <div className="text-xs text-gray-500">{color}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Typography Sample */}
        <div>
          <h4 className="font-semibold mb-2">Typography</h4>
          <div className="space-y-1">
            <h1 className="text-2xl font-bold">Heading 1</h1>
            <h2 className="text-xl font-semibold">Heading 2</h2>
            <h3 className="text-lg font-medium">Heading 3</h3>
            <p className="text-base">Body text with normal weight</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Small text for captions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Theme Customization Component
const ThemeCustomizationFeatures: React.FC = () => {
  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Theme Customization</h1>
          <p className="text-gray-600 dark:text-gray-400">Customize the appearance and behavior of your trading interface</p>
        </div>
        <div className="flex items-center space-x-2">
          <SwatchIcon className="h-6 w-6 text-blue-500" />
          <SwatchIcon className="h-6 w-6 text-purple-500" />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ThemeCustomizationPanel />
          <ThemePreview />
        </div>
      </div>
    </div>
  );
};

export default ThemeCustomizationFeatures;
