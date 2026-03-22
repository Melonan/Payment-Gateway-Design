.PHONY: install
install:
	@poetry install 

.PHONY: run
run:
	@poetry run python3 main.py

.PHONY: test
test: 
	@poetry run python3 -m pytest -vv