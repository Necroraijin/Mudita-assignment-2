import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ma2: {
          50: "#f5f7fa",
          100: "#ebeef3",
          200: "#d2d9e5",
          300: "#aab8cd",
          400: "#7c92b0",
          500: "#5b7597",
          600: "#475e7e",
          700: "#3a4d66",
          800: "#334256",
          900: "#2e3949",
          950: "#1e2531",
        },
      },
    },
  },
  plugins: [],
};

export default config;
