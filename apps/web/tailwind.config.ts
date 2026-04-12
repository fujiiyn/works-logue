import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./contexts/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary
        primary: "#29736B",
        "primary-dark": "#1F3833",
        "primary-light-bg": "#E0F0ED",
        accent: "#00B4CC",

        // Background & Surface
        bg: "#F7F5ED",
        "bg-card": "#FBF9F5",
        border: "#E5E3DB",

        // Text
        "text-secondary": "#596B66",
        "text-muted": "#99998F",
        "text-sage": "#A6B89E",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "var(--font-noto-sans-jp)", "sans-serif"],
      },
      borderRadius: {
        xs: "2px",
        sm: "4px",
        md: "6px",
        lg: "10px",
      },
      fontSize: {
        display: ["28px", { lineHeight: "1.3", fontWeight: "600" }],
        "heading-xl": ["24px", { lineHeight: "1.3", fontWeight: "600" }],
        "heading-l": ["18px", { lineHeight: "1.4", fontWeight: "500" }],
        "heading-m": ["15px", { lineHeight: "1.4", fontWeight: "600" }],
        "body-m": ["13px", { lineHeight: "1.5", fontWeight: "500" }],
        "body-s": ["12px", { lineHeight: "1.5", fontWeight: "500" }],
        caption: ["11px", { lineHeight: "1.4", fontWeight: "500" }],
      },
    },
  },
  plugins: [],
};

export default config;
