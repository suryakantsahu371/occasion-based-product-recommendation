// Captures the README screenshots (light + dark). Requires the backend and `npm run dev` to be running.
//   node scripts/screenshots.mjs            -> ../docs/screenshots/*.png
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const BASE = process.env.BASE_URL ?? "http://127.0.0.1:5173";
const OUT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "docs", "screenshots");
mkdirSync(OUT, { recursive: true });

const settle = (page, ms = 1600) => page.waitForTimeout(ms); // let entrance animations finish

async function search(page, text) {
  const input = page.getByLabel("What's the occasion?");
  await input.fill(text);
  await input.press("Enter");
}

const browser = await chromium.launch();
for (const scheme of ["light", "dark"]) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: scheme });
  const page = await ctx.newPage();
  await page.goto(BASE);
  await page.getByLabel("What's the occasion?").waitFor();
  await settle(page);
  await page.screenshot({ path: join(OUT, `01-input-${scheme}.png`) });

  await page.getByLabel("What's the occasion?").fill("diw");
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(OUT, `02-autocomplete-${scheme}.png`) });

  await search(page, "Diwali");
  await page.getByRole("list", { name: "Recommended products" }).waitFor();
  await page.waitForLoadState("networkidle").catch(() => {});
  await settle(page, 2200);
  await page.screenshot({ path: join(OUT, `03-results-${scheme}.png`), fullPage: true });

  await page.getByRole("button", { name: /view details/i }).first().click();
  await page.waitForTimeout(900);
  await page.screenshot({ path: join(OUT, `04-quickview-${scheme}.png`) });
  await page.keyboard.press("Escape");

  await search(page, "xyzqwerty");
  await page.getByRole("status").waitFor();
  await settle(page);
  await page.screenshot({ path: join(OUT, `05-empty-${scheme}.png`) });
  await ctx.close();
}

// Mobile (375px) results, light mode.
const mobile = await browser.newContext({ viewport: { width: 375, height: 812 }, colorScheme: "light" });
const mpage = await mobile.newPage();
await mpage.goto(BASE);
await search(mpage, "Valentine's Day");
await mpage.getByRole("list", { name: "Recommended products" }).waitFor();
await settle(mpage, 2200);
await mpage.screenshot({ path: join(OUT, "06-results-mobile.png"), fullPage: false });
await browser.close();
console.log("screenshots written to", OUT);
