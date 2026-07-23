.PHONY: install test run demo screenshots

install:
	python3 -m pip install -e ".[test]"

test:
	python3 -m pytest -q

run:
	python3 -m uvicorn omy_mission_plan.app:app --host 0.0.0.0 --port 8000 --reload

demo:
	python3 -m uvicorn omy_mission_plan.app:app --host 0.0.0.0 --port 8000

screenshots:
	node scripts/capture_screenshots.mjs
