.PHONY: help
help:
	@echo "Commands:"
	@echo ".venv          : Create a virtual environment."
	@echo "install        : Install poetry.lock excluding optional dev dependencies."
	@echo "install-dev    : Install poetry.lock including optional dev dependencies."
	@echo "compile        : Update poetry.lock."
	@echo "update-dev     : Update .venv using poetry.lock including optional dev dependencies."
	@echo "test           : Run python tests in ./tests/_0_unit_tests."
	@echo "coverage       : Check test coverage of src/doc_ai/libraries and src/eval_toolkit."

.PHONY: .venv
.venv:
	python -m venv .venv && \
	. .venv/bin/activate && \
	python -m pip install pip setuptools wheel && \
	python -m pip install --upgrade pip && \
	pip install poetry

.PHONY: install-dev
install-dev: .venv
	source .venv/bin/activate && \
	poetry install --with dev --with test

.PHONY: install
install: .venv
	source .venv/bin/activate && \
	poetry install

.PHONY: compile
compile:
	source .venv/bin/activate && \
	poetry lock

.PHONY: update-dev
update-dev:
	source .venv/bin/activate && \
	poetry install --with dev --with test

.PHONY: test
test:
	source .venv/bin/activate && \
	pytest -vx tests/_0_unit_tests

.PHONY: coverage
coverage:
	source .venv/bin/activate && \
	pytest --cov-report term-missing --cov-report html:cov_html --cov=src/doc_ai/libraries --cov=src/eval_toolkit tests/_0_unit_tests

