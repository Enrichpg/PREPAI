/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Brand: naranja-fuego
        brand: {
          50:  '#fff3ed',
          100: '#ffe4cc',
          200: '#ffc695',
          300: '#ff9e5e',
          400: '#ff7035',
          500: '#ff5722',
          600: '#e63900',
          700: '#bf2c00',
          800: '#982300',
          900: '#7a1f00',
        },
        // Accent: verde eléctrico
        accent: {
          50:  '#e6fff7',
          100: '#b3ffea',
          200: '#66ffd4',
          300: '#1affc0',
          400: '#00f0aa',
          500: '#00e5a0',
          600: '#00c288',
          700: '#009966',
          800: '#007750',
          900: '#005540',
        },
        // Surface: oscuros
        surface: {
          50:  '#f0f0f5',
          100: '#d0d0e0',
          200: '#a0a0c0',
          300: '#7070a0',
          400: '#505080',
          500: '#303060',
          600: '#20203a',
          700: '#161628',
          800: '#10101e',
          900: '#0a0a14',
          950: '#060609',
        },
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Bebas Neue"', 'sans-serif'],
      },
      boxShadow: {
        glow:        '0 0 20px rgba(255, 87, 34, 0.35)',
        'glow-accent':'0 0 20px rgba(0, 229, 160, 0.30)',
        glass:       '0 8px 32px rgba(0,0,0,0.5)',
      },
      animation: {
        'fade-up':    'fadeSlideUp 0.35s ease both',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'shimmer':    'shimmer 1.5s linear infinite',
        'spin-slow':  'spin 3s linear infinite',
      },
      keyframes: {
        fadeSlideUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%,100%': { boxShadow: '0 0 0px rgba(255,87,34,0)' },
          '50%':     { boxShadow: '0 0 24px rgba(255,87,34,0.5)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition:  '200% 0' },
        },
      },
    },
  },
  plugins: [],
};

