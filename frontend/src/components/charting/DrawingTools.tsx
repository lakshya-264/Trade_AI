import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Time } from 'lightweight-charts';

// Drawing Tool Types
export interface DrawingPoint {
  time: Time;
  price: number;
}

export interface DrawingConfig {
  id: string;
  type: DrawingToolType;
  points: DrawingPoint[];
  style: DrawingStyle;
  visible: boolean;
  locked: boolean;
  name?: string;
}

export interface DrawingStyle {
  color: string;
  lineWidth: number;
  lineStyle: 'solid' | 'dashed' | 'dotted';
  fillColor?: string;
  fillOpacity?: number;
  text?: string;
  fontSize?: number;
}

export type DrawingToolType = 
  | 'trendline'
  | 'horizontal_line'
  | 'vertical_line'
  | 'fibonacci_retracement'
  | 'fibonacci_extension'
  | 'rectangle'
  | 'ellipse'
  | 'triangle'
  | 'text'
  | 'arrow'
  | 'pitchfork'
  | 'gann_fan'
  | 'measure';

// Drawing Tool Manager
export class DrawingToolManager {
  private drawings: Map<string, DrawingConfig> = new Map();
  private activeTool: DrawingToolType | null = null;
  private isDrawing: boolean = false;
  private currentDrawing: DrawingConfig | null = null;
  private listeners: Array<(drawings: DrawingConfig[]) => void> = [];

  addDrawing(drawing: DrawingConfig) {
    this.drawings.set(drawing.id, drawing);
    this.notifyListeners();
  }

  removeDrawing(id: string) {
    this.drawings.delete(id);
    this.notifyListeners();
  }

  updateDrawing(id: string, updates: Partial<DrawingConfig>) {
    const drawing = this.drawings.get(id);
    if (drawing) {
      this.drawings.set(id, { ...drawing, ...updates });
      this.notifyListeners();
    }
  }

  getDrawings(): DrawingConfig[] {
    return Array.from(this.drawings.values());
  }

  getDrawing(id: string): DrawingConfig | undefined {
    return this.drawings.get(id);
  }

  setActiveTool(tool: DrawingToolType | null) {
    this.activeTool = tool;
  }

  getActiveTool(): DrawingToolType | null {
    return this.activeTool;
  }

  subscribe(listener: (drawings: DrawingConfig[]) => void) {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.getDrawings()));
  }
}

// Drawing Tools Component
interface DrawingToolsProps {
  toolManager: DrawingToolManager;
  onToolSelect?: (tool: DrawingToolType | null) => void;
  className?: string;
}

const DrawingTools: React.FC<DrawingToolsProps> = ({
  toolManager,
  onToolSelect,
  className = ''
}) => {
  const [activeTool, setActiveTool] = useState<DrawingToolType | null>(null);
  const [showStylePanel, setShowStylePanel] = useState(false);
  const [currentStyle, setCurrentStyle] = useState<DrawingStyle>({
    color: '#ff6b6b',
    lineWidth: 2,
    lineStyle: 'solid',
    fillOpacity: 0.2
  });

  const toolButtons = [
    { type: 'trendline' as DrawingToolType, name: 'Trend Line', icon: '📈' },
    { type: 'horizontal_line' as DrawingToolType, name: 'Horizontal Line', icon: '➖' },
    { type: 'vertical_line' as DrawingToolType, name: 'Vertical Line', icon: '📏' },
    { type: 'fibonacci_retracement' as DrawingToolType, name: 'Fibonacci Retracement', icon: '🌀' },
    { type: 'fibonacci_extension' as DrawingToolType, name: 'Fibonacci Extension', icon: '🌀' },
    { type: 'rectangle' as DrawingToolType, name: 'Rectangle', icon: '⬜' },
    { type: 'ellipse' as DrawingToolType, name: 'Ellipse', icon: '⭕' },
    { type: 'triangle' as DrawingToolType, name: 'Triangle', icon: '🔺' },
    { type: 'text' as DrawingToolType, name: 'Text', icon: '📝' },
    { type: 'arrow' as DrawingToolType, name: 'Arrow', icon: '➡️' },
    { type: 'pitchfork' as DrawingToolType, name: 'Pitchfork', icon: '🍴' },
    { type: 'gann_fan' as DrawingToolType, name: 'Gann Fan', icon: '🌪️' },
    { type: 'measure' as DrawingToolType, name: 'Measure', icon: '📐' },
  ];

  const handleToolSelect = useCallback((tool: DrawingToolType) => {
    const newTool = activeTool === tool ? null : tool;
    setActiveTool(newTool);
    toolManager.setActiveTool(newTool);
    onToolSelect?.(newTool);
  }, [activeTool, toolManager, onToolSelect]);

  const handleStyleChange = useCallback((style: Partial<DrawingStyle>) => {
    const newStyle = { ...currentStyle, ...style };
    setCurrentStyle(newStyle);
  }, [currentStyle]);

  return (
    <div className={`drawing-tools ${className}`}>
      {/* Tool Buttons */}
      <div className="tool-buttons flex flex-wrap gap-1 p-2 bg-gray-800 border-b border-gray-700">
        {toolButtons.map((tool) => (
          <button
            key={tool.type}
            onClick={() => handleToolSelect(tool.type)}
            className={`tool-button flex items-center space-x-1 px-3 py-2 rounded text-sm transition-colors ${
              activeTool === tool.type
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title={tool.name}
          >
            <span className="text-lg">{tool.icon}</span>
            <span className="hidden sm:inline">{tool.name}</span>
          </button>
        ))}
        
        <div className="flex-1"></div>
        
        <button
          onClick={() => setShowStylePanel(!showStylePanel)}
          className={`px-3 py-2 rounded text-sm ${
            showStylePanel
              ? 'bg-gray-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          Style
        </button>
      </div>

      {/* Style Panel */}
      {showStylePanel && (
        <div className="style-panel p-4 bg-gray-700 border-b border-gray-600">
          <div className="grid grid-cols-2 gap-4">
            {/* Color */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Color
              </label>
              <input
                type="color"
                value={currentStyle.color}
                onChange={(e) => handleStyleChange({ color: e.target.value })}
                className="w-full h-8 rounded border border-gray-500"
              />
            </div>

            {/* Line Width */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Line Width: {currentStyle.lineWidth}
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={currentStyle.lineWidth}
                onChange={(e) => handleStyleChange({ lineWidth: Number(e.target.value) })}
                className="w-full"
              />
            </div>

            {/* Line Style */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Line Style
              </label>
              <select
                value={currentStyle.lineStyle}
                onChange={(e) => handleStyleChange({ lineStyle: e.target.value as 'solid' | 'dashed' | 'dotted' })}
                className="w-full px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white text-sm"
              >
                <option value="solid">Solid</option>
                <option value="dashed">Dashed</option>
                <option value="dotted">Dotted</option>
              </select>
            </div>

            {/* Fill Opacity */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Fill Opacity: {Math.round((currentStyle.fillOpacity || 0) * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={currentStyle.fillOpacity || 0}
                onChange={(e) => handleStyleChange({ fillOpacity: Number(e.target.value) })}
                className="w-full"
              />
            </div>

            {/* Text Input */}
            {activeTool === 'text' && (
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Text
                </label>
                <input
                  type="text"
                  value={currentStyle.text || ''}
                  onChange={(e) => handleStyleChange({ text: e.target.value })}
                  placeholder="Enter text..."
                  className="w-full px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white text-sm"
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Drawing Instructions */}
      {activeTool && (
        <div className="drawing-instructions p-2 bg-gray-600 text-gray-300 text-sm">
          {getDrawingInstructions(activeTool)}
        </div>
      )}
    </div>
  );
};

// Helper function to get drawing instructions
const getDrawingInstructions = (tool: DrawingToolType): string => {
  const instructions: Record<DrawingToolType, string> = {
    trendline: 'Click two points to draw a trend line',
    horizontal_line: 'Click once to draw a horizontal line',
    vertical_line: 'Click once to draw a vertical line',
    fibonacci_retracement: 'Click two points to draw Fibonacci retracement',
    fibonacci_extension: 'Click two points to draw Fibonacci extension',
    rectangle: 'Click and drag to draw a rectangle',
    ellipse: 'Click and drag to draw an ellipse',
    triangle: 'Click three points to draw a triangle',
    text: 'Click to place text annotation',
    arrow: 'Click and drag to draw an arrow',
    pitchfork: 'Click three points to draw a pitchfork',
    gann_fan: 'Click two points to draw Gann fan',
    measure: 'Click two points to measure distance'
  };
  return instructions[tool] || 'Select a drawing tool to begin';
};

// Drawing Canvas Component
interface DrawingCanvasProps {
  toolManager: DrawingToolManager;
  chartContainer: HTMLElement | null;
  className?: string;
}

const DrawingCanvas: React.FC<DrawingCanvasProps> = ({
  toolManager,
  chartContainer,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentPoints, setCurrentPoints] = useState<DrawingPoint[]>([]);
  const [drawings, setDrawings] = useState<DrawingConfig[]>([]);

  useEffect(() => {
    const unsubscribe = toolManager.subscribe(setDrawings);
    return unsubscribe;
  }, [toolManager]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !chartContainer) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match chart container
    const resizeCanvas = () => {
      const rect = chartContainer.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
    };
  }, [chartContainer]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    const activeTool = toolManager.getActiveTool();
    if (!activeTool) return;

    setIsDrawing(true);
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Convert screen coordinates to chart coordinates
    const point = convertScreenToChart(x, y);
    setCurrentPoints([point]);
  }, [toolManager]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDrawing) return;

    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const point = convertScreenToChart(x, y);
    setCurrentPoints(prev => [...prev.slice(0, -1), point]);
  }, [isDrawing]);

  const handleMouseUp = useCallback(() => {
    if (!isDrawing) return;

    const activeTool = toolManager.getActiveTool();
    if (!activeTool || currentPoints.length === 0) return;

    // Create drawing based on tool type
    const drawing: DrawingConfig = {
      id: `${activeTool}-${Date.now()}`,
      type: activeTool,
      points: [...currentPoints],
      style: {
        color: '#ff6b6b',
        lineWidth: 2,
        lineStyle: 'solid',
        fillOpacity: 0.2
      },
      visible: true,
      locked: false
    };

    toolManager.addDrawing(drawing);
    
    setIsDrawing(false);
    setCurrentPoints([]);
  }, [isDrawing, currentPoints, toolManager]);

  const convertScreenToChart = (x: number, y: number): DrawingPoint => {
    // This is a simplified conversion - in a real implementation,
    // you'd need to convert based on the chart's price and time scales
    return {
      time: Date.now() as Time,
      price: 100 + (y / 10) // Simplified price calculation
    };
  };

  const renderDrawings = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Render existing drawings
    drawings.forEach(drawing => {
      if (!drawing.visible) return;

      ctx.strokeStyle = drawing.style.color;
      ctx.lineWidth = drawing.style.lineWidth;
      ctx.setLineDash(
        drawing.style.lineStyle === 'dashed' ? [5, 5] :
        drawing.style.lineStyle === 'dotted' ? [2, 2] : []
      );

      switch (drawing.type) {
        case 'trendline':
          if (drawing.points.length >= 2) {
            ctx.beginPath();
            ctx.moveTo(0, 0); // Simplified - would need proper coordinate conversion
            ctx.lineTo(canvas.width, canvas.height);
            ctx.stroke();
          }
          break;
        case 'horizontal_line':
          if (drawing.points.length >= 1) {
            ctx.beginPath();
            ctx.moveTo(0, canvas.height / 2);
            ctx.lineTo(canvas.width, canvas.height / 2);
            ctx.stroke();
          }
          break;
        // Add more drawing types as needed
      }
    });

    // Render current drawing in progress
    if (isDrawing && currentPoints.length > 0) {
      ctx.strokeStyle = '#ff6b6b';
      ctx.lineWidth = 2;
      ctx.setLineDash([]);
      
      const activeTool = toolManager.getActiveTool();
      if (activeTool === 'trendline' && currentPoints.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(0, 0); // Simplified
        ctx.lineTo(canvas.width, canvas.height);
        ctx.stroke();
      }
    }
  }, [drawings, isDrawing, currentPoints, toolManager]);

  useEffect(() => {
    renderDrawings();
  }, [renderDrawings]);

  return (
    <canvas
      ref={canvasRef}
      className={`drawing-canvas absolute top-0 left-0 pointer-events-auto ${className}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      style={{ zIndex: 10 }}
    />
  );
};

export default DrawingTools;
export { DrawingCanvas };
