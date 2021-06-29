none: clean

help:
	@echo "make test	test the project"
	@echo
	@echo "make format	run formatters and linters"
	@echo "make lint	alias for format"
	@echo "make prep	format, lint, and test the project in preparation for a pull request"
	@echo
	@echo "make setup	create virtual environment and install pre-commit"
	@echo "make update	update dependencies"
	@echo "make clean	clean up build artifacts"
.PHONY: help

setup:
	poetry install
	poetry run pre-commit install
.PHONY: requirements

format:
	poetry run pre-commit run --all
.PHONY: format

lint: format
.PHONY: lint

test:
	poetry run ward
.PHONY: test

tests:
	test
.PHONY: tests

coverage:
	poetry run coverage run --source=lunchmoney/ -m ward
	poetry run coverage html
	open htmlcov/index.html
.PHONY: coverage

update:
	poetry update
.PHONY: update

prep: setup update lint test
.PHONY: prep

repl:
	poetry run python
.PHONY: repl

clean:
	rm -rf build/
	rm -rf dist/
.PHONY: clean
