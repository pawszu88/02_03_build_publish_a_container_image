APP = $(notdir $(CURDIR))
TAG = $(shell echo "$$(date +%F)-$$(git rev-parse --short HEAD)")

PORT = 3000
NAME = python-api
PYTHON_VERSION = $(shell python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
FMT  = black --check --diff *.py || true
LINT = flake8 --max-line-length=88 --ignore=E203,W503
TEST = python -m pytest --verbose --junit-xml=junit.xml
RUN  = uvicorn main:app --host 0.0.0.0 --port $(PORT) --reload

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[0;33m
NC = \033[0m # No Color

all: setup fmt lint test
	@echo "$(GREEN)All checks passed!$(NC)"

setup:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@pip install --requirement requirements.txt > /dev/null 2>&1
	@echo "$(GREEN)$(NAME) Application Setup complete$(NC)"

fmt:
	@echo "$(GREEN)Running formatter...$(NC)"
	@$(FMT)

lint:
	@echo "$(GREEN)Running linter...$(NC)"
	@$(LINT)

test:
	@echo "$(GREEN)Running tests...$(NC)"
	@$(TEST)

build:
	@echo "$(GREEN)Building container image...$(NC)"
	@docker build -t $(APP):$(TAG) -t $(APP):latest .
	@echo "$(GREEN)Container image built: $(APP):$(TAG)$(NC)"

container-run:
	@echo "$(GREEN)Running container...$(NC)"
	@docker run --rm -p $(PORT):$(PORT) $(APP):latest

run:
	$(RUN)

clean:
	@echo "$(YELLOW)Cleaning generated files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".mypy_cache" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "junit.xml" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(NC)"

.PHONY: setup fmt lint test build container-run run clean all
