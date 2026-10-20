import { chromium } from "playwright-core";
import { mkdir, access } from "node:fs/promises";
import { constants } from "node:fs";

const BASE = process.env.BASE_URL || "http://127.0.0.1:8010";
const OUT = new URL("../docs/screenshots/", import.meta.url);
const ART = process.env.ARTIFACTS_DIR || "/tmp/omp-screenshots";

const CANDIDATES = [
  process.env.CHROME_PATH,
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
  "/usr/local/bin/google-chrome",
  "/usr/bin/google-chrome-stable",
  "/home/tprettol/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome",
  "/home/tprettol/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome",
].filter(Boolean);

async function resolveChrome() {
  for (const p of CANDIDATES) {
    try {
      await access(p, constants.X_OK);
      return p;
    } catch {
      /* try next */
    }
  }
  throw new Error(
    `No Chrome/Chromium found. Set CHROME_PATH. Tried: ${CANDIDATES.join(", ")}`,
  );
}

await mkdir(OUT, { recursive: true });
await mkdir(ART, { recursive: true });

const executablePath = await resolveChrome();
console.log("chrome", executablePath, "base", BASE);

const browser = await chromium.launch({
  executablePath,
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

async function shotViewport(name) {
  const path = new URL(`${name}.png`, OUT).pathname;
  await page.screenshot({ path });
  await page.screenshot({ path: `${ART}/${name}.png` });
  console.log("wrote", name, "(viewport)");
}

async function ensureChecked(sel, on = true) {
  const el = page.locator(sel);
  if (!(await el.count())) return;
  // Toolbar toggles can sit in overflow; drive state directly then notify change.
  await page.evaluate(
    ({ selector, want }) => {
      const input = document.querySelector(selector);
      if (!input) return;
      if (input.checked === want) return;
      input.checked = want;
      input.dispatchEvent(new Event("change", { bubbles: true }));
    },
    { selector: sel, want: on },
  );
  await page.waitForTimeout(200);
}

await page.goto(BASE, { waitUntil: "networkidle" });
await page.waitForSelector(".brand-mark");
await page.waitForTimeout(500);

// Seed a plan so routes / exposure / details have content
await page.click("#btn-plan");
await page.waitForFunction(() => {
  const go = document.querySelector("#stat-go")?.textContent?.trim();
  return go && go !== "—";
}, { timeout: 20000 });
await page.waitForTimeout(600);

// runPlan() finishes by switching to Routes; wait for that to land first,
// otherwise its late setView("routes") overrides the Plan click below.
await page
  .waitForFunction(
    () => document.querySelector(".tab.active")?.dataset.view === "routes",
    { timeout: 20000 },
  )
  .catch(() => {});
await page.waitForTimeout(400);

// Stay on Plan tab for the solid-field shot
await page.click('.tab[data-view="plan"]');
await page.waitForTimeout(300);

// 01 — Plan: solid weather-radar cost field (rings off so the field reads clean)
await ensureChecked("#tog-costgrid", true);
await ensureChecked("#tog-rings", false);
await ensureChecked("#tog-threats", true);
await ensureChecked("#tog-routes", true);
await page.waitForFunction(() => {
  const legend = document.querySelector("#cost-legend");
  const cells = document.querySelectorAll("#map .cost-cell, #map polygon.cost-cell");
  return legend && !legend.hidden && cells.length > 0;
}, { timeout: 20000 });
// Fit theater so jam discs in northern Iraq are in frame (bounds expand with threats).
await page.click("#btn-fit-theater");
await page.waitForTimeout(500);
await shotViewport("01-plan-psab-world");

// 01b — same field filtered to one RF band (S-band) so emitters isolate
const bandSel = page.locator("#sel-frequency-band");
if (await bandSel.count()) {
  const hasS = await page.evaluate(() =>
    [...document.querySelectorAll("#sel-frequency-band option")].some((o) => o.value === "S-band"),
  );
  if (hasS) {
    await bandSel.selectOption("S-band");
    await page.waitForTimeout(800);
    await shotViewport("01b-plan-s-band-weather");
    await bandSel.selectOption("all");
    await page.waitForTimeout(600);
  }
}

// 02 — Options A/B/C
await page.click("#tab-options");
await page.waitForTimeout(400);
await page.click("#btn-top-three");
await page.waitForSelector(".option-card:not(.empty)");
await page.waitForTimeout(1200);
const prefer = page.locator(".option-card .btn-prefer").first();
if (await prefer.count()) {
  await prefer.click();
  await page.waitForTimeout(500);
}
await shot("02-options-top-three");

// 03 — Routes overview
await page.click("#tab-routes");
await page.waitForTimeout(800);
await page.waitForSelector("#routes-tbody tr[data-route]");
await shot("03-routes-overview-metrics");

// 04 — Aligned timeline
await page.click('.subtab[data-routes-pane="timeline"]');
await page.waitForTimeout(800);
await shot("04-aligned-timeline");

// 05 — Details drawer: route-exposure focus + weather Impact rail + jam rails
await page.click('.subtab[data-routes-pane="table"]');
await page.waitForTimeout(300);
// Prefer a deep-threat route so Impact shows green→yellow→orange→red.
const deepThreat = page.locator("#routes-tbody tr[data-route]").filter({ hasText: "Viper-3" });
if (await deepThreat.count()) await deepThreat.first().click();
else await page.locator("#routes-tbody tr[data-route]").first().click();
await page.waitForTimeout(400);
await page.click("#btn-more-details");
await page.waitForSelector("#details-drawer:not([hidden])");
await page.waitForTimeout(900);
await shotViewport("05-route-details-map-threats");

await browser.close();
console.log("done");
