import { build } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const extensionRoot = path.resolve(__dirname, "..");
const distDir = path.resolve(extensionRoot, "dist");

async function buildExtension() {
  console.log("🚀 Starting Chrome Extension build (Manifest V3)...");

  // Clean dist directory
  if (fs.existsSync(distDir)) {
    fs.rmSync(distDir, { recursive: true, force: true });
  }
  fs.mkdirSync(distDir, { recursive: true });

  // 1. Build React Side Panel
  console.log("📦 Building React Side Panel...");
  await build({
    root: path.resolve(extensionRoot, "src/sidepanel"),
    plugins: [react()],
    base: "./",
    build: {
      outDir: path.resolve(distDir, "sidepanel"),
      emptyOutDir: true,
      rollupOptions: {
        input: path.resolve(extensionRoot, "src/sidepanel/index.html"),
      },
    },
    configFile: false,
  });

  // 2. Build Background Service Worker
  console.log("⚙️  Building Service Worker...");
  await build({
    build: {
      outDir: path.resolve(distDir, "background"),
      emptyOutDir: false,
      lib: {
        entry: path.resolve(extensionRoot, "src/background/service-worker.ts"),
        name: "ServiceWorker",
        formats: ["es"],
        fileName: () => "service-worker.js",
      },
      rollupOptions: {
        output: {
          entryFileNames: "service-worker.js",
        },
      },
    },
    configFile: false,
  });

  // 3. Build YouTube Content Script (IIFE for isolated execution)
  console.log("📺 Building YouTube Content Script...");
  await build({
    build: {
      outDir: path.resolve(distDir, "content"),
      emptyOutDir: false,
      lib: {
        entry: path.resolve(extensionRoot, "src/content/youtube-content.ts"),
        name: "YouTubeContent",
        formats: ["iife"],
        fileName: () => "youtube-content.js",
      },
      rollupOptions: {
        output: {
          entryFileNames: "youtube-content.js",
        },
      },
    },
    configFile: false,
  });

  // 4. Copy Manifest V3
  console.log("📋 Copying Manifest V3...");
  const srcManifest = path.resolve(extensionRoot, "src/manifest.json");
  const destManifest = path.resolve(distDir, "manifest.json");
  fs.copyFileSync(srcManifest, destManifest);

  // 5. Copy Icons
  console.log("🎨 Copying icons...");
  const srcIconsDir = path.resolve(extensionRoot, "public/icons");
  const destIconsDir = path.resolve(distDir, "icons");
  fs.mkdirSync(destIconsDir, { recursive: true });

  if (fs.existsSync(srcIconsDir)) {
    const iconFiles = fs.readdirSync(srcIconsDir);
    for (const icon of iconFiles) {
      fs.copyFileSync(path.resolve(srcIconsDir, icon), path.resolve(destIconsDir, icon));
    }
  }

  // Validate build artifacts
  const requiredFiles = [
    path.resolve(distDir, "manifest.json"),
    path.resolve(distDir, "sidepanel/index.html"),
    path.resolve(distDir, "background/service-worker.js"),
    path.resolve(distDir, "content/youtube-content.js"),
    path.resolve(distDir, "icons/icon16.png"),
    path.resolve(distDir, "icons/icon48.png"),
    path.resolve(distDir, "icons/icon128.png"),
  ];

  let missing = false;
  for (const file of requiredFiles) {
    if (!fs.existsSync(file)) {
      console.error(`❌ Missing build artifact: ${file}`);
      missing = true;
    }
  }

  if (missing) {
    throw new Error("Build validation failed: some artifacts were not created.");
  }

  console.log("✅ Chrome Extension build finished successfully!");
  console.log(`📁 Unpacked extension ready at: ${distDir}`);
}

buildExtension().catch((err) => {
  console.error("❌ Build failed:", err);
  process.exit(1);
});

