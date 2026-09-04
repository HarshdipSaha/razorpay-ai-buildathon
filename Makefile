.PHONY: install test demo serve verify-audit report

install:
	pip install -e ".[dev]"

test:
	pytest -q

demo:
	python -m rebound.cli demo

serve:
	python -m rebound.cli serve

verify-audit:
	python -m rebound.cli verify-audit

report:
	python -m rebound.cli report --html
