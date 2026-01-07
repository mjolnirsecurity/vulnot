/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "#1B4F72",
          foreground: "#ffffff",
        },
        secondary: {
          DEFAULT: "#2E86AB",
          foreground: "#ffffff",
        },
        destructive: {
          DEFAULT: "#E74C3C",
          foreground: "#ffffff",
        },
        warning: {
          DEFAULT: "#F39C12",
          foreground: "#000000",
        },
        success: {
          DEFAULT: "#27AE60",
          foreground: "#ffffff",
        },
        muted: {
          DEFAULT: "#6B7280",
          foreground: "#9CA3AF",
        },
        accent: {
          DEFAULT: "#3B82F6",
          foreground: "#ffffff",
        },
        card: {
          DEFAULT: "#1F2937",
          foreground: "#F3F4F6",
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flow': 'flow 2s linear infinite',
      },
      keyframes: {
        flow: {
          '0%': { strokeDashoffset: '0' },
          '100%': { strokeDashoffset: '-20' },
        },
      },
    },
  },
  plugins: [],
}
