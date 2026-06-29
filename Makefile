.PHONY: all setup download etl index models dashboard test lint clean

PYTHON := uv run python
SRC := src

all: setup download etl index models dashboard

setup:
	uv sync --extra dev
	cp -n .env.example .env || true

download:
	$(PYTHON) -m pipeline.download

etl:
	$(PYTHON) -m pipeline.transform

index:
	$(PYTHON) -m src.models.index_builder

models:
	$(PYTHON) -m src.models.trainer

dashboard:
	uv run streamlit run src/dashboard/app.py --server.port 8501

test:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	uv run ruff check src/ pipeline/ tests/
	uv run black --check src/ pipeline/ tests/

format:
	uv run ruff check --fix src/ pipeline/ tests/
	uv run black src/ pipeline/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
