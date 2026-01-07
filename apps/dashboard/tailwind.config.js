/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Industrial HMI color scheme
        hmi: {
          bg: '#1a1a2e',
          panel: '#16213e',
          border: '#0f3460',
          accent: '#e94560',
          success: '#00d26a',
          warning: '#ffc107',
          danger: '#dc3545',
          info: '#17a2b8',
          water: '#3498db',
          chemical: '#9b59b6',
          pipe: '#5d6d7e',
        },
        // Status colors
        status: {
          running: '#00d26a',
          stopped: '#6c757d',
          fault: '#dc3545',
          warning: '#ffc107',
          maintenance: '#17a2b8',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flow': 'flow 2s linear infinite',
        'blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        flow: {
          '0%': { strokeDashoffset: '0' },
          '100%': { strokeDashoffset: '-20' },
        },
        blink: {
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
