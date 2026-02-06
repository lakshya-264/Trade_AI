import React, { useRef, useEffect, useCallback } from 'react';

interface Drawing {
  id: string;
  type: 'trendline' | 'horizontal' | 'vertical' | 'fibonacci' | 'fibonacci_extension' | 'rectangle' | 'circle' | 'text' | 'arrow' | 'ray' | 'parallel_channel' | 'pitchfork' | 'gann_fan' | 'triangle';
  points: Array<{ x: number; y: number }>;
  color: string;
  lineWidth: number;
  text?: string;
  visible: boolean;
}

interface DrawingCanvasOverlayProps {
  chartContainerRef: React.RefObject<HTMLDivElement>;
  drawings: Drawing[];
  currentDrawing: Drawing | null;
  isDrawing: boolean;
  activeTool: string | null;
  onMouseDown: (e: React.MouseEvent) => void;
  onMouseMove: (e: React.MouseEvent) => void;
  onMouseUp: (e: React.MouseEvent) => void;
}

const DrawingCanvasOverlay: React.FC<DrawingCanvasOverlayProps> = ({
  chartContainerRef,
  drawings,
  currentDrawing,
  isDrawing,
  activeTool,
  onMouseDown,
  onMouseMove,
  onMouseUp
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (chartContainerRef.current && canvasRef.current) {
      const updateCanvasSize = () => {
        const container = chartContainerRef.current;
        const canvas = canvasRef.current;
        if (container && canvas) {
          const rect = container.getBoundingClientRect();
          canvas.width = rect.width;
          canvas.height = rect.height;
          redrawAll();
        }
      };

      updateCanvasSize();
      window.addEventListener('resize', updateCanvasSize);
      return () => window.removeEventListener('resize', updateCanvasSize);
    }
  }, [chartContainerRef]);

  const drawShape = useCallback((ctx: CanvasRenderingContext2D, drawing: Drawing) => {
    ctx.strokeStyle = drawing.color;
    ctx.fillStyle = drawing.color;
    ctx.lineWidth = drawing.lineWidth;
    ctx.setLineDash([]);

    if (drawing.points.length === 0) return;

    const start = drawing.points[0];
    const end = drawing.points[drawing.points.length - 1];

    switch (drawing.type) {
      case 'trendline':
      case 'horizontal':
      case 'vertical':
        if (drawing.points.length >= 2) {
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
        }
        break;

      case 'ray':
        if (drawing.points.length >= 2) {
          // Draw infinite ray
          const dx = end.x - start.x;
          const dy = end.y - start.y;
          const length = Math.sqrt(dx * dx + dy * dy);
          const extend = 5000; // Extend ray far beyond canvas
          const scale = extend / length;
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(start.x + dx * scale, start.y + dy * scale);
          ctx.stroke();
        }
        break;

      case 'parallel_channel':
        if (drawing.points.length >= 2) {
          // Draw two parallel lines forming a channel
          const dx = end.x - start.x;
          const dy = end.y - start.y;
          const channelWidth = 50; // Default channel width
          const perpX = -dy;
          const perpY = dx;
          const perpLength = Math.sqrt(perpX * perpX + perpY * perpY);
          const perpScale = channelWidth / perpLength;
          
          // Top line
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
          
          // Bottom line (parallel)
          ctx.beginPath();
          ctx.moveTo(start.x + perpX * perpScale, start.y + perpY * perpScale);
          ctx.lineTo(end.x + perpX * perpScale, end.y + perpY * perpScale);
          ctx.stroke();
          
          // Connect lines
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(start.x + perpX * perpScale, start.y + perpY * perpScale);
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(end.x, end.y);
          ctx.lineTo(end.x + perpX * perpScale, end.y + perpY * perpScale);
          ctx.stroke();
        }
        break;

      case 'rectangle':
        if (drawing.points.length >= 2) {
          const rectWidth = end.x - start.x;
          const rectHeight = end.y - start.y;
          ctx.strokeRect(start.x, start.y, rectWidth, rectHeight);
        }
        break;

      case 'circle':
        if (drawing.points.length >= 2) {
          const radius = Math.sqrt(
            Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2)
          );
          ctx.beginPath();
          ctx.arc(start.x, start.y, radius, 0, 2 * Math.PI);
          ctx.stroke();
        }
        break;

      case 'triangle':
        if (drawing.points.length >= 3) {
          ctx.beginPath();
          ctx.moveTo(drawing.points[0].x, drawing.points[0].y);
          ctx.lineTo(drawing.points[1].x, drawing.points[1].y);
          ctx.lineTo(drawing.points[2].x, drawing.points[2].y);
          ctx.closePath();
          ctx.stroke();
        }
        break;

      case 'fibonacci':
        if (drawing.points.length >= 2) {
          const fibLevels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
          const priceRange = Math.abs(end.y - start.y);
          fibLevels.forEach(level => {
            const y = start.y + (priceRange * level * (end.y > start.y ? 1 : -1));
            ctx.beginPath();
            ctx.moveTo(start.x, y);
            ctx.lineTo(end.x, y);
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);
            
            ctx.fillStyle = drawing.color;
            ctx.font = '10px Arial';
            ctx.fillText(`${(level * 100).toFixed(1)}%`, end.x + 5, y + 3);
          });
        }
        break;

      case 'fibonacci_extension':
        if (drawing.points.length >= 3) {
          // Fibonacci extension uses 3 points: start, retrace, extension
          const [p1, p2, p3] = [drawing.points[0], drawing.points[1], drawing.points[2]];
          const baseRange = Math.abs(p2.y - p1.y);
          const fibExtLevels = [0, 0.382, 0.618, 1, 1.382, 1.618, 2, 2.618];
          const direction = p2.y > p1.y ? -1 : 1;
          
          fibExtLevels.forEach(level => {
            const y = p2.y + (baseRange * level * direction);
            ctx.beginPath();
            ctx.moveTo(p1.x, y);
            ctx.lineTo(p3.x, y);
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);
            
            ctx.fillStyle = drawing.color;
            ctx.font = '10px Arial';
            ctx.fillText(`${(level * 100).toFixed(1)}%`, p3.x + 5, y + 3);
          });
        }
        break;

      case 'pitchfork':
        if (drawing.points.length >= 3) {
          // Andrews Pitchfork: 3 points - pivot, high, low
          const [pivot, high, low] = [drawing.points[0], drawing.points[1], drawing.points[2]];
          const midX = (high.x + low.x) / 2;
          const midY = (high.y + low.y) / 2;
          
          // Center line from pivot through midpoint
          ctx.beginPath();
          ctx.moveTo(pivot.x, pivot.y);
          ctx.lineTo(midX, midY);
          const extendX = midX + (midX - pivot.x) * 2;
          const extendY = midY + (midY - pivot.y) * 2;
          ctx.lineTo(extendX, extendY);
          ctx.stroke();
          
          // Upper parallel line
          const upperOffset = high.y - midY;
          ctx.beginPath();
          ctx.moveTo(high.x, high.y);
          const upperExtendX = extendX;
          const upperExtendY = extendY + upperOffset;
          ctx.lineTo(upperExtendX, upperExtendY);
          ctx.stroke();
          
          // Lower parallel line
          const lowerOffset = low.y - midY;
          ctx.beginPath();
          ctx.moveTo(low.x, low.y);
          const lowerExtendX = extendX;
          const lowerExtendY = extendY + lowerOffset;
          ctx.lineTo(lowerExtendX, lowerExtendY);
          ctx.stroke();
        }
        break;

      case 'gann_fan':
        if (drawing.points.length >= 1) {
          // Gann Fan: 8 lines at specific angles from a point
          const center = drawing.points[0];
          const angles = [1, 2, 3, 4, 5, 6, 7, 8]; // Gann angles
          const length = 1000; // Extend far
          
          angles.forEach((angle, idx) => {
            // Gann angles: 1x1, 1x2, 1x3, etc. (in price/time ratio)
            const radians = Math.atan(1 / angle);
            const x = center.x + length * Math.cos(radians);
            const y = center.y - length * Math.sin(radians); // Negative for upward trend
            
            ctx.beginPath();
            ctx.moveTo(center.x, center.y);
            ctx.lineTo(x, y);
            ctx.setLineDash([3, 3]);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Label
            ctx.fillStyle = drawing.color;
            ctx.font = '8px Arial';
            ctx.fillText(`1:${angle}`, x + 5, y);
          });
        }
        break;

      case 'arrow':
        if (drawing.points.length >= 2) {
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
          const angle = Math.atan2(end.y - start.y, end.x - start.x);
          const arrowLength = 10;
          ctx.beginPath();
          ctx.moveTo(end.x, end.y);
          ctx.lineTo(
            end.x - arrowLength * Math.cos(angle - Math.PI / 6),
            end.y - arrowLength * Math.sin(angle - Math.PI / 6)
          );
          ctx.moveTo(end.x, end.y);
          ctx.lineTo(
            end.x - arrowLength * Math.cos(angle + Math.PI / 6),
            end.y - arrowLength * Math.sin(angle + Math.PI / 6)
          );
          ctx.stroke();
        }
        break;

      case 'text':
        if (drawing.text && drawing.points.length >= 1) {
          ctx.font = `${drawing.lineWidth * 8}px Arial`;
          ctx.fillText(drawing.text, start.x, start.y);
        }
        break;
    }
  }, []);

  const redrawAll = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    drawings.filter(d => d.visible).forEach(drawing => {
      drawShape(ctx, drawing);
    });

    if (currentDrawing && isDrawing) {
      drawShape(ctx, currentDrawing);
    }
  }, [drawings, currentDrawing, isDrawing, drawShape]);

  useEffect(() => {
    redrawAll();
  }, [redrawAll]);

  if (!chartContainerRef.current) return null;

  return (
    <canvas
      ref={canvasRef}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={(e) => onMouseUp(e)}
      className="pointer-events-auto cursor-crosshair"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 10,
        pointerEvents: activeTool ? 'auto' : 'none'
      }}
    />
  );
};

export default DrawingCanvasOverlay;

