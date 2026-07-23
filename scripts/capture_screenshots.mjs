import { chromium } from "playwright-core";
import { mkdir } from "node:fs/promises";

const BASE = process.env.BASE_URL || "http://127.0.0.1:8000";
const OUT = new URL("../docs/screenshots/", import.meta.url);
const ART = "/opt/cursor/artifacts/screenshots";

await mkdir(OUT, { recursive: true });
await mkdir(ART, { recursive: true });

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || "/usr/local/bin/google-chrome",
  headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

async function shot(name) {
  const path = new URL(`${name}.png`, OUT).pathname;
  await page.screenshot({ path, fullPage: true });
  await page.screenshot({ path: `${ART}/${name}.png`, fullPage: true });
  console.log("wrote", name);
}

await page.goto(BASE, { waitUntil: "networkidle" });
await page.waitForSelector(".brand-mark");
await page.waitForTimeout(600);
await shot("01-initial-dark-ui");

await page.click("#btn-plan");
await page.waitForTimeout(1200);
await shot("02-plan-cycle-go-nogo");

// Select a fighter and insert
const fighter = page.locator('[data-aircraft="FTR-1"]');
if (await fighter.count()) await fighter.click();
await page.fill("#insert-id", "STK-SHOT");
await page.click("#btn-insert-submit");
await page.waitForTimeout(1200);
await shot("03-dynamic-insert-reassess");

// Open help for IxDF panel
await page.locator(".help").evaluate((el) => {
  el.open = true;
});
await page.waitForTimeout(400);
await shot("04-ixdf-help-panel");

await browser.close();
console.log("done");
