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
      },
      animation: {
        shimmer: 'shimmer 2s ease-in-out infinite',
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
          50: '#f6f6f6',
          100: '#e7e7e7',
          200: '#d1d1d1',
          300: '#b0b0b0',
          400: '#888888',
          500: '#6d6d6d',
          600: '#5d5d5d',
          700: '#4f4f4f',
          800: '#454545',
          900: '#262626',
          950: '#171717',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
