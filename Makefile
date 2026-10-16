.PHONY: install test run demo screenshots

install:
	python3 -m pip install -e ".[test]"

test:
	python3 -m pytest -q

run:
	python3 -m uvicorn omy_mission_plan.app:app --host 0.0.0.0 --port 8010 --reload

demo:
	python3 -m uvicorn omy_mission_plan.app:app --host 0.0.0.0 --port 8010

screenshots:
	BASE_URL=$${BASE_URL:-http://127.0.0.1:8010} CHROME_PATH=$${CHROME_PATH:-/usr/bin/chromium} node scripts/capture_screenshots.mjs
