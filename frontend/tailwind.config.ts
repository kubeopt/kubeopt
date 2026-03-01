import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'spin-slow': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        shimmer: 'shimmer 2s ease-in-out infinite',
        fadeIn: 'fadeIn 200ms ease-out',
        'spin-slow': 'spin-slow 8s linear infinite',
      },
      colors: {
        primary: {
          50: '#f2f8ef',
          100: '#e0eeda',
          200: '#c3deb8',
          300: '#9ec88d',
          400: '#7fb069',
          500: '#5f9548',
          600: '#4a7737',
          700: '#3a5c2d',
          800: '#314a28',
          900: '#2a3f23',
          950: '#132210',
        },
        dark: {
          50: '#e8edf5',
          100: '#c8d5e8',
          200: '#a3b8d4',
          300: '#8fa4c4',
          400: '#5a7499',
          500: '#3d5a80',
          600: '#2a4066',
          700: '#1e3050',
          800: '#172742',
          900: '#111a2e',
          950: '#0b1222',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
