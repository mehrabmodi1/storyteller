/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'bg-amber-950',
    'bg-indigo-950',
    'bg-slate-900',
    'bg-red-950',
    'bg-cyan-950',
    'bg-amber-900',
    'bg-indigo-900',
    'bg-slate-800',
    'bg-red-900',
    'bg-cyan-900',
    'bg-amber-700',
    'bg-indigo-700',
    'bg-slate-700',
    'bg-red-800',
    'bg-cyan-700',
    'hover:bg-amber-600',
    'hover:bg-indigo-600',
    'hover:bg-slate-600',
    'hover:bg-red-700',
    'hover:bg-cyan-600',
    'focus:ring-amber-500',
    'focus:ring-indigo-500',
    'focus:ring-slate-500',
    'focus:ring-red-500',
    'focus:ring-cyan-500',
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors for persona themes will be applied dynamically via style prop
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
    },
  },
  plugins: [],
}

