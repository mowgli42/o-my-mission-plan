.PHONY: install test run demo

install:
	python3 -m pip install -e ".[test]"

test:
	python3 -m pytest -q

run:
	uvicorn omy_mission_plan.app:app --host 0.0.0.0 --port 8000 --reload

demo:
	uvicorn omy_mission_plan.app:app --host 0.0.0.0 --port 8000
