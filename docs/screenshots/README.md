# Screenshots

Captured from the running FastAPI UI (`make demo` → http://localhost:8000).

| File | Scene |
|------|-------|
| `01-initial-dark-ui.png` | Fresh demo world before planning |
| `02-plan-cycle-go-nogo.png` | After **Run plan cycle** — assignments, routes, status strip |
| `03-dynamic-insert-reassess.png` | After inserting `STK-SHOT` on FTR-1 |
| `04-ixdf-help-panel.png` | Expanded IxDF / shortcuts help |

Regenerate:

```bash
# server already on :8000
npm install
node scripts/capture_screenshots.mjs
```
