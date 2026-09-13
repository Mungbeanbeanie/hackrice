import { readFileSync, writeFileSync } from "node:fs";
import * as esbuild from "esbuild";

// Dev defaults — no real deploy domain exists yet (deploy/README.md: both
// boxes are bare IP, no TLS). Set both env vars once one does.
const apiBaseUrl = process.env.EXTENSION_API_BASE_URL ?? "http://localhost:8000";
const webappUrl = process.env.EXTENSION_WEBAPP_URL ?? "http://localhost:5173";

const template = readFileSync("manifest.template.json", "utf8");
const manifest = template.replace("__API_ORIGIN__", new URL(apiBaseUrl).origin);
writeFileSync("manifest.json", manifest);

try {
  await esbuild.build({
    entryPoints: ["src/content.ts", "src/background.ts"],
    bundle: true,
    outdir: ".",
    format: "iife",
    define: {
      API_BASE_URL: JSON.stringify(apiBaseUrl),
      WEBAPP_URL: JSON.stringify(webappUrl),
    },
  });
} catch {
  process.exit(1);
}
