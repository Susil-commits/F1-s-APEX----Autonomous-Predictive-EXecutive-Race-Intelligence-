/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        apex: {
          bg: "#06090e",
          bgDark: "#030508",
          card: "#0c1322",
          cardHover: "#141f36",
          panel: "#0f172a",
          border: "#1e293b",
          borderGlow: "#334155",
          cyan: "#00f0ff",
          cyanGlow: "rgba(0, 240, 255, 0.4)",
          red: "#ef4444",
          yellow: "#eab308",
          amber: "#f59e0b",
          green: "#10b981",
          emerald: "#059669",
          purple: "#a855f7",
          sectorPurple: "#c084fc",
          muted: "#64748b",
          slateText: "#94a3b8",
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scanline': 'scanline 8s linear infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite alternate',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        },
        glowPulse: {
          '0%': { opacity: '0.6', filter: 'drop-shadow(0 0 4px rgba(0, 240, 255, 0.4))' },
          '100%': { opacity: '1', filter: 'drop-shadow(0 0 12px rgba(0, 240, 255, 0.9))' },
        },
      },
    },
  },
  plugins: [],
}
