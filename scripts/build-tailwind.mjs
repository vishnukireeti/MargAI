#!/usr/bin/env node
// Precompiles the Tailwind utilities this app actually uses into a static CSS file
// (assets/tailwind.css), replacing the cdn.tailwindcss.com runtime JIT compiler.
//
// Run this any time Tailwind classes are added/removed/changed in index.html:
//   node scripts/build-tailwind.mjs
//
// How it works: scans index.html as plain text for anything that *looks* like a
// utility class (Tailwind's own extractor does the same thing — it doesn't parse
// HTML/JS, it just tokenizes). Over-matching is harmless (bogus tokens are
// silently dropped by the compiler); under-matching would silently drop real
// styles, so the tokenizer here is deliberately broad.

import { compile } from 'tailwindcss';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const htmlPath = path.join(repoRoot, 'index.html');
const outPath = path.join(repoRoot, 'assets', 'tailwind.css');

const html = readFileSync(htmlPath, 'utf8');

// Broad tokenizer: split on characters that can never appear inside a Tailwind
// candidate (quotes, angle brackets, '=', whitespace, ';', braces) and keep
// everything else as one token — this preserves arbitrary-value classes like
// `text-[11px]` or `shadow-[0_0_0_3px_rgba(0,0,0,.1)]` intact.
const tokens = new Set(html.split(/["'`<>=\s;{}]+/).filter(Boolean));
const candidates = [...tokens];

// Same brand palette as the old `tailwind.config` JS object in index.html —
// keep these two in sync if the brand colour ever changes.
const css = `
@import "tailwindcss";

@theme {
  --color-brand-50: #eff6ff;
  --color-brand-100: #dbeafe;
  --color-brand-200: #bfdbfe;
  --color-brand-300: #93c5fd;
  --color-brand-400: #60a5fa;
  --color-brand-500: #3b82f6;
  --color-brand-600: #2563eb;
  --color-brand-700: #1d4ed8;
  --color-brand-800: #1e40af;
  --color-brand-900: #1e3a8a;
  --color-brand-950: #172554;
}
`;

// Resolve `@import "tailwindcss"` (and any package it in turn imports) against
// real node_modules package.json "exports"/"style" fields, same as a bundler would.
async function loadStylesheet(id, base) {
    if (id === 'tailwindcss') {
        const pkgPath = require.resolve('tailwindcss/package.json', { paths: [base] });
        const pkgDir = path.dirname(pkgPath);
        const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
        const entry = pkg.style || pkg.exports?.['.']?.style || 'index.css';
        const fullPath = path.join(pkgDir, entry);
        return { path: fullPath, base: path.dirname(fullPath), content: readFileSync(fullPath, 'utf8') };
    }
    throw new Error(`Don't know how to resolve stylesheet import "${id}" (base: ${base})`);
}

const { build } = await compile(css, { base: repoRoot, loadStylesheet });
let output = build(candidates);

// Minify: Tailwind's compile() output here isn't minified by default without
// lightningcss wired in as a postcss step; do a safe, conservative minification
// (strip comments and collapse whitespace) rather than pull in a bundler.
output = output
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/\s+/g, ' ')
  .replace(/\s*([{}:;,])\s*/g, '$1')
  .replace(/;}/g, '}')
  .trim();

writeFileSync(outPath, output);
console.log(`Wrote ${outPath} (${(output.length / 1024).toFixed(1)} KB, ${candidates.length} candidate tokens scanned)`);
