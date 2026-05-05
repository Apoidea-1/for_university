import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        app: "#07111f",
        panel: "#0f1729",
        panelSoft: "#132038",
        borderSoft: "rgba(148, 163, 184, 0.18)",
        accent: "#14b8a6",
        accentStrong: "#0f766e",
        sand: "#f4e4c1",
      },
      fontFamily: {
        sans: ["Manrope", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        panel: "0 25px 60px rgba(2, 8, 23, 0.35)",
      },
      backgroundImage: {
        mesh: "radial-gradient(circle at top left, rgba(20,184,166,0.18), transparent 36%), radial-gradient(circle at bottom right, rgba(244,228,193,0.12), transparent 28%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
