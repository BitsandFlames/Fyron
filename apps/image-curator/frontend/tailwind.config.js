export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ember: "#FF6A1A",
        amber: "#FDBA3B",
        violet: "#8E7CC3",
        bf: {
          ink: "#0B0B0C",
          obsidian: "#080A0F",
          panel: "#111319",
          panel2: "#171A21",
          panel3: "#1F2430",
          line: "rgba(255,255,255,0.12)",
          text: "#F8FAFC",
          muted: "#A7AAB4",
          subtle: "#D7D2C6",
          cream: "#FFFAF1",
          ember: "#FF6A1A",
          ember2: "#FDBA3B",
          blue: "#4D9ED8",
          teal: "#5B8E7D",
          coral: "#E56B6F",
          violet: "#8E7CC3",
          grape: "#332E55",
          gold: "#F2A65A"
        }
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      boxShadow: {
        ember: "0 0 0 1px rgba(255,106,26,.36), 0 18px 46px rgba(0,0,0,.34)",
        panel: "0 18px 60px rgba(0,0,0,.28)"
      }
    }
  },
  plugins: []
};
