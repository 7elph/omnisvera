import { useEffect, useRef } from "react";

type Props = { densityByCell: Record<string, number>; columns: number; rows: number };

export default function MistParticleOverlay({ densityByCell, columns, rows }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const width = Math.max(1, rect.width); const height = Math.max(1, rect.height);
      const ratio = Math.min(window.devicePixelRatio || 1, 1.25);
      canvas.width = Math.floor(width * ratio); canvas.height = Math.floor(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      context.clearRect(0, 0, width, height);
      const cellWidth = width / columns;
      const cellHeight = height / rows;
      const radius = Math.max(cellWidth, cellHeight) * .82;
      Object.entries(densityByCell).forEach(([cell, rawDensity]) => {
        const [column, row] = cell.split(":").map(Number);
        if (!Number.isFinite(column) || !Number.isFinite(row)) return;
        const density = Math.max(0, Math.min(1, rawDensity));
        if (density <= 0) return;
        const centerX = (column + .5) * cellWidth;
        const centerY = (row + .5) * cellHeight;
        const gradient = context.createRadialGradient(centerX, centerY, radius * .18, centerX, centerY, radius);
        gradient.addColorStop(0, `rgba(247,249,250,${density * .9})`);
        gradient.addColorStop(.58, `rgba(235,240,243,${density * .7})`);
        gradient.addColorStop(1, "rgba(225,232,236,0)");
        context.fillStyle = gradient;
        context.beginPath();
        context.arc(centerX, centerY, radius, 0, Math.PI * 2);
        context.fill();
      });
    };
    const observer = new ResizeObserver(draw);
    observer.observe(canvas); draw();
    return () => observer.disconnect();
  }, [densityByCell, columns, rows]);

  return <canvas ref={canvasRef} className="map-mist-particles" aria-hidden="true" />;
}
