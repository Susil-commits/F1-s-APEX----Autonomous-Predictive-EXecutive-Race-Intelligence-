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
          // Official Formula 1 Racing Red & Accents
          red: "#E10600",
          redHover: "#FF1801",
          redDark: "#B30000",
          redGlow: "rgba(225, 6, 0, 0.5)",
          
          // Deep Carbon Black & Chassis Tones
          bg: "#08090C",
          bgDark: "#030406",
          card: "#0E1017",
          cardHover: "#151821",
          panel: "#12151E",
          border: "#1F2432",
          borderGlow: "rgba(225, 6, 0, 0.45)",
          
          // Crisp Titanium Whites & Telemetry Accents
          white: "#FFFFFF",
          slateText: "#E2E8F0",
          muted: "#8A94A6",
          
          // Supporting FIA Telemetry Colors
          cyan: "#00F0FF",
          yellow: "#FFD000",
          amber: "#FF8C00",
          green: "#00E676",
          emerald: "#00C853",
          purple: "#C084FC",
          sectorPurple: "#D946EF",
        },
        f1: {
          red: "#E10600",
          darkRed: "#9E0000",
          carbon: "#0E1017",
          carbonDark: "#060709",
          slate: "#1C202B",
          white: "#FFFFFF",
          silver: "#E5E7EB",
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scanline': 'scanline 8s linear infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite alternate',
        'f1-pulse': 'f1Pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        },
        glowPulse: {
          '0%': { opacity: '0.6', filter: 'drop-shadow(0 0 4px rgba(225, 6, 0, 0.4))' },
          '100%': { opacity: '1', filter: 'drop-shadow(0 0 14px rgba(225, 6, 0, 0.95))' },
        },
        f1Pulse: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.85', transform: 'scale(1.02)' },
        }
      },
    },
  },
  plugins: [],
}
