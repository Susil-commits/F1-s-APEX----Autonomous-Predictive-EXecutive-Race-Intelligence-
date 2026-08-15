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
          bg: "#080c14",
          card: "#0f172a",
          cardHover: "#1e293b",
          border: "#1e293b",
          cyan: "#00f0ff",
          red: "#ef4444",
          yellow: "#eab308",
          green: "#22c55e",
          purple: "#a855f7",
          muted: "#64748b",
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
