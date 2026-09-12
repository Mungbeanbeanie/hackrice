import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

// Flat config is just an array — no helper needed.
export default [
  // design_handoff_nectarly_production/ is reference material (design
  // prototypes authored as streaming HTML, not app code) — never linted,
  // typechecked, or built.
  { ignores: ["dist/**", "design_handoff_nectarly_production/**"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...reactHooks.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: { globals: globals.browser },
  },
];
