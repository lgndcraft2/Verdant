import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "media",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)", "Lexend", "sans-serif"],
        body: ["var(--font-body)", "Source Sans 3", "sans-serif"],
      },
      boxShadow: {
        soft: "0 30px 80px -40px rgba(15, 23, 42, 0.45)",
      },
      backgroundImage: {
        "hero-grid":
          "linear-gradient(rgba(225, 29, 72, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(225, 29, 72, 0.06) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};

export default config;
