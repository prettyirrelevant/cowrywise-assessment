LINT_PATHS = packages/

ifneq (,$(wildcard ./.env.local))
    include .env.local
    export
endif

lint:
	@ruff check

lint-fix:
	@ruff check $(LINT_PATHS) --fix

format:
	@ruff format $(LINT_PATHS)

test-pagekeeper:
	@echo "Running pagekeeper tests..."
	uv run --package=pagekeeper pytest -s packages/pagekeeper

test-bookworm:
	@echo "Running bookworm tests..."
	uv run --package=bookworm packages/bookworm/bookworm/manage.py test bookworm.apps.books -v 2

test-librarian:
	@echo "Running librarian tests..."
	uv run --package=librarian packages/librarian/librarian/manage.py test librarian.apps.books -v 2

librarian-consumer:
	@echo "Running librarian consumer..."
	uv run --package=librarian packages/librarian/librarian/manage.py process_events

librarian-dev:
	@echo "creating & running migrations..."
	uv run --package=librarian packages/librarian/librarian/manage.py makemigrations && uv run --package=librarian packages/librarian/librarian/manage.py migrate

	@echo "starting librarian server..."
	uv run --package=librarian packages/librarian/librarian/manage.py runserver 0.0.0.0:8084

librarian-migrations:
	@echo "creating & running migrations..."
	uv run --package=librarian packages/librarian/librarian/manage.py makemigrations books
	uv run --package=librarian packages/librarian/librarian/manage.py migrate

bookworm-consumer:
	@echo "Running bookworm consumer..."
	uv run --package=bookworm packages/bookworm/bookworm/manage.py process_events

bookworm-dev:
	@echo "creating & running migrations..."
	uv run --package=bookworm packages/bookworm/bookworm/manage.py makemigrations && uv run --package=bookworm packages/bookworm/bookworm/manage.py migrate

	@echo "starting bookworm server..."
	uv run --package=bookworm packages/bookworm/bookworm/manage.py runserver 0.0.0.0:8080

bookworm-migrations:
	@echo "creating & running migrations..."
	uv run --package=bookworm packages/bookworm/bookworm/manage.py makemigrations books
	uv run --package=bookworm packages/bookworm/bookworm/manage.py migrate

pagekeeper-dev:
	@echo "starting pagekeeper server..."
	uv run --refresh --package=pagekeeper packages/pagekeeper/pagekeeper/server.py
