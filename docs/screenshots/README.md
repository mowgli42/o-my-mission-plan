# Screenshots

Captured from the running FastAPI UI (`make demo` → http://localhost:8010).

| File | Scene |
|------|-------|
| `01-plan-psab-world.png` | Plan tab — solid weather-radar cost field (hex), legend with max aggregation |
| `02-options-top-three.png` | Options — A/B/C archetypes + compare |
| `03-routes-overview-metrics.png` | Routes table + metrics |
| `04-aligned-timeline.png` | Multi-platform TOT timeline |
| `05-route-details-map-threats.png` | More details — route exposure, inset theater field, severity badges |

Regenerate:

```bash
make demo   # in one terminal (port 8010)
make screenshots
# or: BASE_URL=http://127.0.0.1:8010 CHROME_PATH=/usr/bin/chromium npm run screenshots
```

The capture script runs a plan cycle first, enables the cost field (rings off)
for shot 01, builds top-three options, then opens the details drawer for
route-exposure shot 05.
