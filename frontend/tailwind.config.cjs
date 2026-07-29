module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        severity: {
          critical: "#f87171",
          high: "#fb923c",
          medium: "#facc15",
          low: "#4ade80",
        },
        surface: {
          DEFAULT: "#0f172a",
          raised: "#1e293b",
          border: "#334155",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};
