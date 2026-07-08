/**
 * Page-render check: opens every page of the running app in headless Chromium,
 * screenshots it, and fails on any JavaScript error.
 *
 * Usage (app must already be running on http://127.0.0.1:8000):
 *   npm install --no-save playwright   (run from the PROJECT ROOT, not frontend/ —
 *     Node resolves node_modules by walking up from this file's own folder, so an
 *     install inside frontend/ is never found here)
 *   node scripts/check_app.mjs
 *
 * In Claude Code remote sessions Chromium is pre-installed at /opt/pw-browsers/chromium.
 * On a Mac, run `npx playwright install chromium` once first (also from the project root).
 * Screenshots land in scripts/screenshots/ — look at them; the check only proves
 * "no JS errors", not "looks right".
 */
import { chromium } from 'playwright';
import { mkdirSync, existsSync } from 'fs';

const BASE = process.env.APP_URL || 'http://127.0.0.1:8000';
const OUT = new URL('./screenshots/', import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });

const PAGES = [
  ['/', 'map'],
  ['/authority/E07000223', 'authority'],
  ['/league', 'league'],
  ['/compare', 'compare'],
  ['/trends', 'trends'],
  ['/dictionary', 'dictionary'],
];

const exePath = existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined;
const browser = await chromium.launch(exePath ? { executablePath: exePath } : {});
const errors = [];

for (const [scheme, suffix] of [['light', ''], ['dark', '-dark']]) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, colorScheme: scheme });
  page.on('pageerror', (e) => errors.push(`${scheme} pageerror: ${e.message}`));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(`${scheme} console: ${m.text()}`); });
  for (const [path, name] of PAGES) {
    await page.goto(BASE + path, { waitUntil: 'networkidle' });
    await page.waitForTimeout(700);
    await page.screenshot({ path: `${OUT}${name}${suffix}.png` });
    console.log(`ok ${scheme} ${path}`);
  }
  await page.close();
}
await browser.close();

if (errors.length) {
  console.error('\nFAILED — JavaScript errors found:\n' + errors.join('\n'));
  process.exit(1);
}
console.log(`\nPASSED — all ${PAGES.length} pages rendered in light and dark with no JS errors.`);
console.log(`Screenshots: ${OUT}`);
