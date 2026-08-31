/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0284c7',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        teal: {
          500: '#14b8a6',
          600: '#0d9488',
        },
        medical: {
          primary: '#0ea5e9',
          secondary: '#14b8a6',
          accent: '#6366f1',
          dark: '#0f172a',
          card: '#ffffff',
          alert: '#ef4444',
          success: '#10b981',
          warning: '#f59e0b'
        }
      },
      fontFamily: {
        sans: ['Inter', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
        'card-hover': '0 20px 30px -10px rgba(2, 132, 199, 0.12)',
      }
    },
  },
  plugins: [],
}
