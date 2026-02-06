import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  PencilIcon,
  MinusIcon,
  Square3Stack3DIcon,
  XMarkIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { httpClient } from '../config/api';
import DrawingCanvasOverlay from './DrawingCanvasOverlay';

interface Drawing {
  id: string;
  type: 'trendline' | 'horizontal' | 'vertical' | 'fibonacci' | 'fibonacci_extension' | 'rectangle' | 'circle' | 'text' | 'arrow' | 'ray' | 'parallel_channel' | 'pitchfork' | 'gann_fan' | 'triangle';
  points: Array<{ x: number; y: number }>;
  color: string;
  lineWidth: number;
  text?: string;
  visible: boolean;
  locked: boolean;
}

interface ChartDrawingToolsProps {
  chartContainerRef: React.RefObject<HTMLDivElement>;
  symbol?: string; // Symbol for saving/loading drawings
  chartApi?: any; // Lightweight Charts API instance for snap-to-price
  candlestickSeries?: any; // Candlestick series for snap-to-price
  onDrawingComplete?: (drawing: Drawing) => void;
  renderOverlay?: (overlayProps: {
    drawings: Drawing[];
    currentDrawing: Drawing | null;
    isDrawing: boolean;
    activeTool: string | null;
    onMouseDown: (e: React.MouseEvent) => void;
    onMouseMove: (e: React.MouseEvent) => void;
    onMouseUp: (e: React.MouseEvent) => void;
  }) => React.ReactNode;
}

const ChartDrawingTools: React.FC<ChartDrawingToolsProps> = ({
  chartContainerRef,
  symbol,
  chartApi,
  candlestickSeries,
  onDrawingComplete,
  renderOverlay
}) => {
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [drawings, setDrawings] = useState<Drawing[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentDrawing, setCurrentDrawing] = useState<Drawing | null>(null);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [showDrawingsList, setShowDrawingsList] = useState(false);
  const [selectedDrawing, setSelectedDrawing] = useState<string | null>(null);
  const [drawingColor, setDrawingColor] = useState('#3B82F6');
  const [lineWidth, setLineWidth] = useState(2);
  const [snapToPrice, setSnapToPrice] = useState(true); // Snap-to-price enabled by default
  const [showTemplates, setShowTemplates] = useState(false);
  

  const tools = [
    // Trend Tools
    { id: 'trendline', name: 'Trend Line', icon: '📈', color: '#3B82F6', category: 'trend', minPoints: 2, maxPoints: 2 },
    { id: 'horizontal', name: 'Horizontal', icon: '➖', color: '#10B981', category: 'trend', minPoints: 1, maxPoints: 1 },
    { id: 'vertical', name: 'Vertical', icon: '📏', color: '#F59E0B', category: 'trend', minPoints: 1, maxPoints: 1 },
    { id: 'ray', name: 'Ray', icon: '↗️', color: '#8B5CF6', category: 'trend', minPoints: 2, maxPoints: 2 },
    { id: 'parallel_channel', name: 'Parallel Channel', icon: '═', color: '#EC4899', category: 'trend', minPoints: 2, maxPoints: 2 },
    
    // Fibonacci Tools
    { id: 'fibonacci', name: 'Fibonacci Retracement', icon: '🌀', color: '#8B5CF6', category: 'fibonacci', minPoints: 2, maxPoints: 2 },
    { id: 'fibonacci_extension', name: 'Fibonacci Extension', icon: '🌀', color: '#A855F7', category: 'fibonacci', minPoints: 3, maxPoints: 3 },
    
    // Advanced Tools
    { id: 'pitchfork', name: 'Pitchfork', icon: '🍴', color: '#F59E0B', category: 'advanced', minPoints: 3, maxPoints: 3 },
    { id: 'gann_fan', name: 'Gann Fan', icon: '🌪️', color: '#10B981', category: 'advanced', minPoints: 1, maxPoints: 1 },
    
    // Geometry Tools
    { id: 'rectangle', name: 'Rectangle', icon: '▭', color: '#EF4444', category: 'geometry', minPoints: 2, maxPoints: 2 },
    { id: 'circle', name: 'Circle', icon: '◯', color: '#06B6D4', category: 'geometry', minPoints: 2, maxPoints: 2 },
    { id: 'triangle', name: 'Triangle', icon: '🔺', color: '#F97316', category: 'geometry', minPoints: 3, maxPoints: 3 },
    { id: 'arrow', name: 'Arrow', icon: '➡️', color: '#84CC16', category: 'geometry', minPoints: 2, maxPoints: 2 },
    
    // Text Tools
    { id: 'text', name: 'Text', icon: '📝', color: '#F97316', category: 'text', minPoints: 1, maxPoints: 1 },
  ];


  // Snap y-coordinate to nearest price level
  const snapYToPrice = (y: number): number => {
    if (!snapToPrice || !candlestickSeries || !chartContainerRef.current) {
      return y;
    }
    
    try {
      const price = candlestickSeries.coordinateToPrice(y);
      if (price !== null && price !== undefined) {
        // Snap to the price level
        const snappedY = candlestickSeries.priceToCoordinate(price);
        return snappedY !== null && snappedY !== undefined ? snappedY : y;
      }
    } catch (error) {
      console.debug('Snap to price failed:', error);
    }
    
    return y;
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!activeTool || !chartContainerRef.current) return;

    const rect = chartContainerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    
    // Snap to price if enabled
    y = snapYToPrice(y);

    const tool = tools.find(t => t.id === activeTool);
    const newDrawing: Drawing = {
      id: `drawing_${Date.now()}`,
      type: activeTool as any,
      points: [{ x, y }],
      color: drawingColor,
      lineWidth,
      visible: true,
      locked: false
    };

    if (activeTool === 'text') {
      const text = window.prompt('Enter text:');
      if (text) {
        newDrawing.text = text;
        newDrawing.points.push({ x: x + 50, y: y + 20 });
        setDrawings([...drawings, newDrawing]);
        onDrawingComplete?.(newDrawing);
        toast.success('Text annotation added');
        setActiveTool(null);
      }
      return;
    }

    // For Gann Fan, only needs 1 point
    if (activeTool === 'gann_fan') {
      setDrawings([...drawings, newDrawing]);
      onDrawingComplete?.(newDrawing);
      toast.success('Gann Fan added');
      setActiveTool(null);
      return;
    }

    setStartPoint({ x, y });
    setCurrentDrawing(newDrawing);
    setIsDrawing(true);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDrawing || !currentDrawing || !chartContainerRef.current) return;

    const rect = chartContainerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    
    // Snap to price if enabled
    y = snapYToPrice(y);

    const tool = tools.find(t => t.id === currentDrawing.type);
    const minPoints = tool?.minPoints || 2;
    const maxPoints = tool?.maxPoints || 2;

    // Update the last point or add new point based on tool requirements
    let updatedPoints = [...currentDrawing.points];
    
    if (updatedPoints.length < minPoints) {
      // Still collecting points
      if (updatedPoints.length === 1) {
        updatedPoints.push({ x, y });
      } else {
        updatedPoints[updatedPoints.length - 1] = { x, y };
      }
    } else if (updatedPoints.length < maxPoints) {
      // Update last point for multi-point tools
      updatedPoints[updatedPoints.length - 1] = { x, y };
    } else {
      // Update last point
      updatedPoints[updatedPoints.length - 1] = { x, y };
    }

    const updatedDrawing = {
      ...currentDrawing,
      points: updatedPoints
    };

    setCurrentDrawing(updatedDrawing);
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (!isDrawing || !currentDrawing) return;

    const tool = tools.find(t => t.id === currentDrawing.type);
    const minPoints = tool?.minPoints || 2;
    const maxPoints = tool?.maxPoints || 2;

    // For multi-point tools, check if we need more clicks
    if (currentDrawing.points.length < minPoints) {
      // Need more points - don't finish yet
      if (e.detail === 1) { // Single click
        const rect = chartContainerRef.current?.getBoundingClientRect();
        if (rect) {
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          setCurrentDrawing({
            ...currentDrawing,
            points: [...currentDrawing.points, { x, y }]
          });
        }
      }
      return;
    }

    // Tool is complete - save it
    setDrawings([...drawings, currentDrawing]);
    onDrawingComplete?.(currentDrawing);
    setCurrentDrawing(null);
    setIsDrawing(false);
    setStartPoint(null);
    toast.success('Drawing added');
  };

  const deleteDrawing = (id: string) => {
    setDrawings(drawings.filter(d => d.id !== id));
    toast.success('Drawing deleted');
  };

  const toggleVisibility = (id: string) => {
    setDrawings(drawings.map(d =>
      d.id === id ? { ...d, visible: !d.visible } : d
    ));
  };

  const saveDrawings = async () => {
    // Save to localStorage as backup
    localStorage.setItem(`drawings_${chartContainerRef.current?.id || 'default'}`, JSON.stringify(drawings));
    
    // Save to backend if symbol is provided
    if (symbol) {
      try {
        for (const drawing of drawings) {
          await httpClient.post('/api/charting/drawing-tools', {
            tool_type: drawing.type,
            symbol: symbol,
            points: drawing.points,
            properties: {
              color: drawing.color,
              lineWidth: drawing.lineWidth,
              text: drawing.text
            }
          });
        }
        toast.success('Drawings saved to cloud');
      } catch (error) {
        console.error('Failed to save drawings to backend:', error);
        toast.success('Drawings saved locally');
      }
    } else {
      toast.success('Drawings saved locally');
    }
  };

  const loadDrawings = async () => {
    // Try loading from backend first
    if (symbol) {
      try {
        const response = await httpClient.get(`/api/charting/drawing-tools/${symbol}`);
        if (response.success && response.data && Array.isArray(response.data)) {
          const backendDrawings: Drawing[] = response.data.map((d: any) => ({
            id: d.id || `drawing_${Date.now()}_${Math.random()}`,
            type: d.tool_type as Drawing['type'],
            points: d.points || [],
            color: d.properties?.color || '#3B82F6',
            lineWidth: d.properties?.lineWidth || 2,
            text: d.properties?.text,
            visible: true,
            locked: false
          }));
          setDrawings(backendDrawings);
          toast.success(`Loaded ${backendDrawings.length} drawings from cloud`);
          return;
        }
      } catch (error) {
        console.error('Failed to load drawings from backend:', error);
      }
    }
    
    // Fallback to localStorage
    const saved = localStorage.getItem(`drawings_${chartContainerRef.current?.id || 'default'}`);
    if (saved) {
      setDrawings(JSON.parse(saved));
      toast.success('Drawings loaded from local storage');
    } else {
      toast.error('No saved drawings found');
    }
  };

  // Load drawings on mount if symbol is provided
  useEffect(() => {
    if (symbol) {
      loadDrawings();
    }
  }, [symbol]);

  // Drawing Templates Functions
  const saveTemplate = () => {
    if (drawings.length === 0) {
      toast.error('No drawings to save as template');
      return;
    }
    
    const templateName = window.prompt('Enter template name:');
    if (!templateName) return;
    
    const template = {
      name: templateName,
      drawings: drawings,
      created_at: new Date().toISOString(),
      symbol: symbol || 'generic'
    };
    
    const templates = JSON.parse(localStorage.getItem('drawing_templates') || '[]');
    templates.push(template);
    localStorage.setItem('drawing_templates', JSON.stringify(templates));
    toast.success(`Template "${templateName}" saved`);
  };

  const loadTemplate = (template: any) => {
    setDrawings(template.drawings);
    toast.success(`Template "${template.name}" loaded`);
    setShowTemplates(false);
  };

  const deleteTemplate = (index: number) => {
    const templates = JSON.parse(localStorage.getItem('drawing_templates') || '[]');
    templates.splice(index, 1);
    localStorage.setItem('drawing_templates', JSON.stringify(templates));
    toast.success('Template deleted');
  };

  const getTemplates = () => {
    return JSON.parse(localStorage.getItem('drawing_templates') || '[]');
  };

  // Export drawings as image
  const exportAsImage = async () => {
    if (!chartContainerRef.current) {
      toast.error('Chart container not found');
      return;
    }
    
    try {
      // Dynamically import html2canvas
      const html2canvas = (await import('html2canvas')).default;
      const container = chartContainerRef.current;
      
      if (!container) {
        toast.error('Chart container not found');
        return;
      }
      
      const canvas = await html2canvas(container, {
        backgroundColor: '#131722',
        scale: 2,
        logging: false,
        useCORS: true
      });
      
      canvas.toBlob((blob) => {
        if (!blob) {
          toast.error('Failed to export image');
          return;
        }
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `drawings_${symbol || 'chart'}_${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success('Drawings exported as image');
      }, 'image/png');
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export image. Make sure html2canvas is installed.');
    }
  };

  return (
    <div className="relative h-full flex">
      {/* Drawing Tools Sidebar */}
      <div className="w-16 bg-[#1e222d]/95 backdrop-blur-sm border-r border-[#2a2e39] flex flex-col items-center py-4 gap-2 overflow-y-auto">
        {tools.map((tool) => (
          <button
            key={tool.id}
            onClick={() => setActiveTool(activeTool === tool.id ? null : tool.id)}
            className={`w-12 h-12 flex items-center justify-center rounded hover:bg-[#2a2e39] transition-colors ${
              activeTool === tool.id ? 'bg-[#2a2e39] border-2 border-blue-500' : 'text-gray-400'
            }`}
            title={tool.name}
          >
            <span className="text-xl">{tool.icon}</span>
          </button>
        ))}
        
        <div className="border-t border-[#2a2e39] my-2 w-full" />
        
        <button
          onClick={() => setShowDrawingsList(!showDrawingsList)}
          className="w-12 h-12 flex items-center justify-center rounded hover:bg-[#2a2e39] text-gray-400"
          title="Manage Drawings"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        
        <button
          onClick={saveDrawings}
          className="w-12 h-12 flex items-center justify-center rounded hover:bg-[#2a2e39] text-gray-400"
          title="Save Drawings"
        >
          <ArrowDownTrayIcon className="w-5 h-5" />
        </button>
        
        <button
          onClick={loadDrawings}
          className="w-12 h-12 flex items-center justify-center rounded hover:bg-[#2a2e39] text-gray-400"
          title="Load Drawings"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </button>
        
        <div className="border-t border-[#2a2e39] my-2 w-full" />
        
        <button
          onClick={() => setSnapToPrice(!snapToPrice)}
          className={`w-12 h-12 flex items-center justify-center rounded hover:bg-[#2a2e39] transition-colors ${
            snapToPrice ? 'bg-green-600/20 text-green-400' : 'text-gray-400'
          }`}
          title={snapToPrice ? 'Snap to Price: ON' : 'Snap to Price: OFF'}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        </button>
        
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          className="w-12 h-12 flex items-center justify-center rounded hover:bg-[#2a2e39] text-gray-400"
          title="Templates"
        >
          <Square3Stack3DIcon className="w-5 h-5" />
        </button>
        
        <button
          onClick={exportAsImage}
          className="w-12 h-12 flex items-center justify-center rounded hover:bg-[#2a2e39] text-gray-400"
          title="Export as Image"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
      </div>

      {/* Drawing Canvas Overlay - Render via prop if provided, otherwise render here */}
      {renderOverlay ? (
        renderOverlay({
          drawings,
          currentDrawing,
          isDrawing,
          activeTool,
          onMouseDown: handleMouseDown,
          onMouseMove: handleMouseMove,
          onMouseUp: handleMouseUp
        })
      ) : (
        <DrawingCanvasOverlay
          chartContainerRef={chartContainerRef}
          drawings={drawings}
          currentDrawing={currentDrawing}
          isDrawing={isDrawing}
          activeTool={activeTool}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        />
      )}

      {/* Drawings List Panel */}
      {showDrawingsList && (
        <div className="absolute top-16 right-4 w-80 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl z-50 max-h-96 overflow-y-auto">
          <div className="p-4 border-b border-[#2a2e39] flex items-center justify-between">
            <h3 className="font-semibold text-white">Drawings ({drawings.length})</h3>
            <button
              onClick={() => setShowDrawingsList(false)}
              className="text-gray-400 hover:text-white"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
          
          <div className="p-4 space-y-2">
            {drawings.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No drawings yet. Select a tool to start drawing.
              </div>
            ) : (
              drawings.map((drawing) => (
                <div
                  key={drawing.id}
                  className="flex items-center justify-between p-2 rounded bg-[#131722] hover:bg-[#2a2e39]"
                >
                  <div className="flex items-center gap-2 flex-1">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: drawing.color }}
                    />
                    <span className="text-sm text-white">{drawing.type}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => toggleVisibility(drawing.id)}
                      className="p-1 text-gray-400 hover:text-white"
                    >
                      {drawing.visible ? (
                        <EyeIcon className="w-4 h-4" />
                      ) : (
                        <EyeSlashIcon className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => deleteDrawing(drawing.id)}
                      className="p-1 text-gray-400 hover:text-red-500"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Color and Width Controls */}
          <div className="p-4 border-t border-[#2a2e39] space-y-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Color</label>
              <div className="flex gap-2">
                {['#3B82F6', '#10B981', '#EF4444', '#F59E0B', '#8B5CF6', '#06B6D4'].map(color => (
                  <button
                    key={color}
                    onClick={() => setDrawingColor(color)}
                    className={`w-8 h-8 rounded border-2 ${
                      drawingColor === color ? 'border-white' : 'border-transparent'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Line Width: {lineWidth}px</label>
              <input
                type="range"
                min="1"
                max="5"
                value={lineWidth}
                onChange={(e) => setLineWidth(Number(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Templates Panel */}
      {showTemplates && (
        <div className="absolute top-16 left-16 ml-2 w-80 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl z-50 max-h-96 overflow-y-auto">
          <div className="p-4 border-b border-[#2a2e39] flex items-center justify-between">
            <h3 className="font-semibold text-white">Drawing Templates</h3>
            <button
              onClick={() => setShowTemplates(false)}
              className="text-gray-400 hover:text-white"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
          
          <div className="p-4 space-y-2">
            {getTemplates().length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No templates saved yet.
              </div>
            ) : (
              getTemplates().map((template: any, index: number) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded bg-[#131722] hover:bg-[#2a2e39]"
                >
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-white">{template.name}</div>
                    <div className="text-xs text-gray-400">
                      {template.drawings?.length || 0} drawings • {new Date(template.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => loadTemplate(template)}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                    >
                      Load
                    </button>
                    <button
                      onClick={() => deleteTemplate(index)}
                      className="p-1 text-gray-400 hover:text-red-500"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
          
          <div className="p-4 border-t border-[#2a2e39]">
            <button
              onClick={saveTemplate}
              className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors"
            >
              Save Current as Template
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChartDrawingTools;
