
# Makefile for common development tasks

# Use python from virtual env if available
VENV_ACTIVATE = source venv/bin/activate

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

format:
	@echo "Formatting code with black..."
	black .

lint:
	@echo "Running flake8 lint checks..."
	flake8 .

test:
	@echo "Running test suite..."
	python -m unittest discover -v

# If using pytest instead:
# test:
# 	pytest tests/ -v

run-example:
	@echo "Running complete workflow example..."
	python examples/complete_workflow_example.py

# Additional convenience targets

sentiment-model-download:
	@echo "Downloading FinBERT model weights (cache)..."
	python -c "from transformers import AutoModel; AutoModel.from_pretrained('ProsusAI/finbert')"
	@echo "FinBERT model downloaded."

clean:
	@echo "Cleaning up pyc files..."
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

