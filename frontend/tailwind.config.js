/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        foreground: "var(--color-foreground)",
        card: "var(--color-card)",
        muted: "var(--color-muted)",
        secondary: "var(--color-secondary)",
        border: "var(--color-border)",
        accent: "#06b6d4",
        accent2: "#3b82f6",
        accent3: "#8b5cf6",
        success: "#22c55e",
        danger: "#ef4444",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
