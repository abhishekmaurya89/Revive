/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0E1512",
        surface: "#141C19",
        raised: "#1B2521",
        border: "#26332D",
        text: "#EDEFEA",
        muted: "#8FA098",
        amber: "#F2A93B",
        teal: "#37C2A4",
        red: "#E5584A",
        blue: "#5B8DEF",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        mono: ["IBM Plex Mono", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        sm: "3px",
        md: "5px",
      },
    },
  },
  plugins: [],
};
