import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// VITE_BASE is set by the Pages workflow so assets resolve under /<repo>/.
export default defineConfig({
  base: process.env.VITE_BASE || "/",
  plugins: [react()],
  test: { environment: "node" },
});
