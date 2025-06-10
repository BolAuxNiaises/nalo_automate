# Makefile for Nalo Ice Cream Automate
# Professional Django development workflow

.PHONY: help install run clean test lint format check init mock serve logs shell migrate docs build commit cz-commit bump changelog

# Default target
help:	## Show this help message
	@echo "Nalo Ice Cream Automate - Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# Development environment
install:	## Install dependencies and setup environment
	python -m venv venv || true
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed"

init:	## Initialize project for first time (migrations + mock data)
	. venv/bin/activate && python manage.py makemigrations ice_cream
	. venv/bin/activate && python manage.py migrate
	. venv/bin/activate && python manage.py init_flavors
	@echo "✅ Project initialized with database and flavors"

mock:	## Generate mock data for testing
	. venv/bin/activate && python manage.py generate_sample_orders --count 10
	@echo "✅ Mock data generated"

# Server management
run:	## Run development server
	. venv/bin/activate && python manage.py runserver

serve:	## Alternative to run (same as run)
	$(MAKE) run

logs:	## Show server logs (if running in background)
	tail -f nohup.out

# Database operations
migrate:	## Apply database migrations
	. venv/bin/activate && python manage.py makemigrations
	. venv/bin/activate && python manage.py migrate
	@echo "✅ Migrations applied"

shell:	## Open Django shell
	. venv/bin/activate && python manage.py shell

# Cleaning
clean:	## Clean cache and temporary files
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyo" -delete
	find . -name ".coverage" -delete
	find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cache and temporary files cleaned"

# Code quality
format:	## Format code with black and isort
	. venv/bin/activate && black --line-length 88 .
	. venv/bin/activate && isort --profile black .
	@echo "✅ Code formatted with black and isort"

lint:	## Run linting with flake8 and pylint
	. venv/bin/activate && flake8 --max-line-length=88 --extend-ignore=E203,W503 .
	. venv/bin/activate && pylint --load-plugins=pylint_django --django-settings-module=nalo_automate.settings ice_cream/ nalo_automate/ || true
	@echo "✅ Linting completed"

check:	## Run all code quality checks
	$(MAKE) format
	$(MAKE) lint
	. venv/bin/activate && python manage.py check
	@echo "✅ All code quality checks completed"

fix:	## Auto-fix common issues
	. venv/bin/activate && autopep8 --in-place --aggressive --aggressive --recursive .
	. venv/bin/activate && black --line-length 88 .
	. venv/bin/activate && isort --profile black .
	@echo "✅ Auto-fixes applied"

# Testing
test:	## Run all tests
	. venv/bin/activate && python manage.py test --verbosity=2

test-coverage:	## Run tests with coverage report
	. venv/bin/activate && coverage run --source='.' manage.py test
	. venv/bin/activate && coverage report
	. venv/bin/activate && coverage html
	@echo "✅ Tests completed with coverage report in htmlcov/"

test-fast:	## Run tests without coverage (faster)
	. venv/bin/activate && python manage.py test --parallel --keepdb

# Commitizen
commit: cz-commit
cz-commit:
	@echo "Starting interactive commit..."
	cz commit

bump:
	@echo "Bumping version..."
	cz bump

bump-dry:
	@echo "Dry run version bump..."
	cz bump --dry-run

changelog:
	@echo "Generating changelog..."
	cz changelog

pre-commit-install:
	@echo "Installing pre-commit hooks..."
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg

validate-commit:
	cz check --rev-range HEAD

# Documentation
docs:	## Generate API documentation
	@echo "📚 API Documentation available at:"
	@echo "  - Swagger UI: http://127.0.0.1:8000/api/docs/"
	@echo "  - ReDoc: http://127.0.0.1:8000/api/redoc/"
	@echo "  - Schema: http://127.0.0.1:8000/api/schema/"


# Development workflow
dev:	## Complete development setup
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) init
	$(MAKE) mock
	$(MAKE) check
	$(MAKE) test
	@echo "🚀 Development environment ready!"
	@echo "Run 'make run' to start the server"

# Quick commands
quick-test:	## Quick test run (most common)
	$(MAKE) clean
	$(MAKE) format
	$(MAKE) test-fast

restart:	## Clean restart
	$(MAKE) clean
	$(MAKE) run

kill-server:	## Kill any running server on port 8000
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@echo "✅ Server killed"

# Status
status:	## Show project status
	@echo "📊 Nalo Ice Cream Automate Status:"
	@echo ""
	@echo "🐍 Python environment:"
	@. venv/bin/activate && python --version
	@echo ""
	@echo "📦 Django status:"
	@. venv/bin/activate && python manage.py check --deploy 2>/dev/null && echo "✅ Django OK" || echo "❌ Django issues"
	@echo ""
	@echo "🗄️  Database:"
	@. venv/bin/activate && python manage.py showmigrations --plan | tail -5
	@echo ""
	@echo "🍦 Flavors in DB:"
	@. venv/bin/activate && python manage.py shell -c "from ice_cream.models import Flavor; print(f'{Flavor.objects.count()} flavors')" 2>/dev/null || echo "Not initialized"
	@echo ""
	@echo "📋 Available commands: make help"