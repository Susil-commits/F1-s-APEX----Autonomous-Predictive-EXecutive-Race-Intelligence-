import React, { useEffect, useRef, useState } from 'react';

interface Parallax3DBackgroundProps {
  src: string;
  alt: string;
  intensity?: number;
  spotlightColor?: string;
  gradientPlacement?: 'hero' | 'circuit' | 'predictor';
  showDepthGrid?: boolean;
  className?: string;
}

export const Parallax3DBackground: React.FC<Parallax3DBackgroundProps> = ({
  src,
  alt,
  intensity = 1.0,
  spotlightColor = 'rgba(225, 6, 0, 0.18)',
  gradientPlacement = 'hero',
  showDepthGrid = true,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 }); // -1 to 1
  const [cursorCoords, setCursorCoords] = useState({ x: 50, y: 50 }); // percentage

  useEffect(() => {
    let animFrameId: number;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      targetX = (e.clientX / innerWidth) * 2 - 1;
      targetY = (e.clientY / innerHeight) * 2 - 1;
      setCursorCoords({
        x: Math.round((e.clientX / innerWidth) * 100),
        y: Math.round((e.clientY / innerHeight) * 100),
      });
    };

    // Smooth spring lerp animation loop
    const animate = () => {
      currentX += (targetX - currentX) * 0.08;
      currentY += (targetY - currentY) * 0.08;
      setMousePos({ x: currentX, y: currentY });
      animFrameId = requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    animFrameId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animFrameId);
    };
  }, []);

  // Compute 3D transforms
  const rotateX = -mousePos.y * 6 * intensity;
  const rotateY = mousePos.x * 10 * intensity;
  const translateX = mousePos.x * 24 * intensity;
  const translateY = mousePos.y * 18 * intensity;

  // Counter parallax for depth grid
  const gridTranslateX = -mousePos.x * 40 * intensity;
  const gridTranslateY = -mousePos.y * 28 * intensity;

  return (
    <div
      ref={containerRef}
      className={`absolute inset-0 overflow-hidden pointer-events-none perspective-1000 z-0 ${className}`}
      style={{ perspective: '1200px' }}
    >
      {/* Primary 3D Photo Layer */}
      <div
        className="absolute inset-[-5%] w-[110%] h-[110%] transition-transform duration-75 ease-out will-change-transform"
        style={{
          transform: `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translate3d(${translateX}px, ${translateY}px, 0px) scale3d(1.06, 1.06, 1.06)`,
          transformStyle: 'preserve-3d',
        }}
      >
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-cover object-center opacity-65 dark:opacity-60 contrast-110 saturate-110 drop-shadow-2xl transition-opacity duration-500"
        />

        {/* 3D Specular Interactive Spotlight */}
        <div
          className="absolute inset-0 pointer-events-none transition-opacity duration-300"
          style={{
            background: `radial-gradient(circle 800px at ${cursorCoords.x}% ${cursorCoords.y}%, ${spotlightColor} 0%, transparent 65%)`,
            mixBlendMode: 'screen',
          }}
        />
      </div>

      {/* Optical Depth Grid / Telemetry Scanning Wireframe (Secondary 3D Depth Layer) */}
      {showDepthGrid && (
        <div
          className="absolute inset-[-10%] w-[120%] h-[120%] pointer-events-none opacity-20 dark:opacity-25 transition-transform duration-75 ease-out will-change-transform"
          style={{
            transform: `perspective(1200px) rotateX(${rotateX * 1.3}deg) rotateY(${rotateY * 1.3}deg) translate3d(${gridTranslateX}px, ${gridTranslateY}px, 40px)`,
            backgroundImage: `
              linear-gradient(to right, rgba(225, 6, 0, 0.15) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(225, 6, 0, 0.15) 1px, transparent 1px)
            `,
            backgroundSize: '80px 80px',
            transformStyle: 'preserve-3d',
          }}
        />
      )}

      {/* Smart Contrast Vignette & Edge Blending Overlays */}
      {gradientPlacement === 'hero' && (
        <>
          {/* Asymmetric left fade for text legibility, preserving right car visuals */}
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--bg-primary)] via-[var(--bg-primary)]/80 via-50% to-transparent to-95%" />
          <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-primary)] via-transparent to-[var(--bg-primary)]/60" />
          <div className="absolute inset-0 bg-gradient-to-b from-[var(--bg-primary)]/40 via-transparent to-[var(--bg-primary)]" />
        </>
      )}

      {gradientPlacement === 'circuit' && (
        <>
          {/* Holographic atmospheric fade */}
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--bg-primary)] via-[var(--bg-primary)]/70 to-[var(--bg-primary)]/85" />
          <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-primary)] via-transparent to-[var(--bg-primary)]" />
        </>
      )}

      {gradientPlacement === 'predictor' && (
        <>
          {/* Subtle frosted glass backdrop for predictor panels */}
          <div className="absolute inset-0 bg-[var(--bg-primary)]/75 backdrop-blur-[2px]" />
          <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-primary)] via-transparent to-[var(--bg-primary)]/80" />
          <div className="absolute inset-0 bg-gradient-to-b from-[var(--bg-primary)]/70 via-transparent to-[var(--bg-primary)]" />
        </>
      )}
    </div>
  );
};
