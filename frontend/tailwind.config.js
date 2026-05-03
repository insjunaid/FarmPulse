/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors
        dark: {
          bg: '#070D14',
          card: '#0F1824',
          border: '#1E293B',
        },
        // Accent color - Cyan
        accent: {
          DEFAULT: '#00E5D4',
          hover: '#00CCBB',
          light: '#4DFFE8',
        },
        // Signal colors
        signal: {
          green: '#22C55E',
          'green-dark': '#16A34A',
          amber: '#F59E0B',
          'amber-dark': '#D97706',
          red: '#EF4444',
          'red-dark': '#DC2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
