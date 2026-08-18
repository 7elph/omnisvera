import { useEffect, useRef } from "react";

type Props = { densityByCell: Record<string, number>; columns: number; rows: number };

export default function MistParticleOverlay({ densityByCell, columns, rows }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    const sampleDensity = (normalizedX: number, normalizedY: number) => {
      const x = Math.max(0, Math.min(columns - 1, normalizedX * columns - .5));
      const y = Math.max(0, Math.min(rows - 1, normalizedY * rows - .5));
      const x0 = Math.floor(x); const y0 = Math.floor(y);
      const x1 = Math.min(columns - 1, x0 + 1); const y1 = Math.min(rows - 1, y0 + 1);
      const tx = x - x0; const ty = y - y0;
      const value = (column: number, row: number) => densityByCell[`${column}:${row}`] || 0;
      const top = value(x0, y0) * (1 - tx) + value(x1, y0) * tx;
      const bottom = value(x0, y1) * (1 - tx) + value(x1, y1) * tx;
      return top * (1 - ty) + bottom * ty;
    };
    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const width = Math.max(1, rect.width); const height = Math.max(1, rect.height);
      const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = Math.floor(width * ratio); canvas.height = Math.floor(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      const pixels = context.createImageData(canvas.width, canvas.height);
      for (let y = 0; y < canvas.height; y += 1) {
        for (let x = 0; x < canvas.width; x += 1) {
          const density = Math.max(0, Math.min(1, sampleDensity((x + .5) / canvas.width, (y + .5) / canvas.height)));
          const index = (y * canvas.width + x) * 4;
          pixels.data[index] = 247; pixels.data[index + 1] = 249; pixels.data[index + 2] = 250;
          pixels.data[index + 3] = Math.round(density * 255);
        }
      }
      context.clearRect(0, 0, width, height);
      context.putImageData(pixels, 0, 0);
    };
    const observer = new ResizeObserver(draw);
    observer.observe(canvas); draw();
    return () => observer.disconnect();
  }, [densityByCell, columns, rows]);

  return <canvas ref={canvasRef} className="map-mist-particles" aria-hidden="true" />;
}
