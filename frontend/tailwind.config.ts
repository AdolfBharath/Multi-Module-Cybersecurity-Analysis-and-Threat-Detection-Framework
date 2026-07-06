import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        abyss: "#071018",
        panel: "rgba(13, 25, 38, 0.78)",
        line: "rgba(140, 164, 190, 0.18)",
        cyanx: "#35d3ff",
        mintx: "#3df2b7",
        amberx: "#f4b860",
        dangerx: "#ff526d"
      },
      boxShadow: {
        glow: "0 0 45px rgba(53, 211, 255, 0.16)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
} satisfies Config;

