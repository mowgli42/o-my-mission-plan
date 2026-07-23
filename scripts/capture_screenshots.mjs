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
await page.waitForTimeout(700);
await shot("01-plan-psab-world");

await page.click("#btn-plan");
await page.waitForTimeout(1500);
await page.waitForSelector("#routes-tbody tr[data-route]");
await shot("02-routes-overview-metrics");

// Select a strike-heavy route if present, else first
const rows = page.locator("#routes-tbody tr[data-route]");
await rows.first().click();
await page.waitForTimeout(500);
await shot("03-route-timeline-events");

await page.click("#btn-more-details");
await page.waitForTimeout(800);
await page.waitForSelector("#details-drawer:not([hidden])");
await shot("04-route-details-map-threats");

await browser.close();
console.log("done");
