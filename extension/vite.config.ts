import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  root: path.resolve(__dirname, "src/sidepanel"),
  build: {
    outDir: path.resolve(__dirname, "dist/sidepanel"),
    emptyOutDir: false,
  },
});

