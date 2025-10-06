import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  safelist: [
    // Backgrounds
    'bg-amber-950', 'bg-indigo-950', 'bg-slate-900', 'bg-red-950', 'bg-cyan-950',
    // Buttons
    'bg-amber-700', 'bg-indigo-700', 'bg-slate-700', 'bg-red-800', 'bg-cyan-700',
    // Button hovers
    'hover:bg-amber-600', 'hover:bg-indigo-600', 'hover:bg-slate-600', 'hover:bg-red-700', 'hover:bg-cyan-600',
    // Inputs
    'bg-amber-900', 'bg-indigo-900', 'bg-slate-800', 'bg-red-900', 'bg-cyan-900',
    // Focus rings
    'focus:ring-amber-500', 'focus:ring-indigo-500', 'focus:ring-slate-500', 'focus:ring-red-500', 'focus:ring-cyan-500',
  ],
  theme: {
    extend: {
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
export default config; 