PYTHON      := python3
PIP         := pip
MODULE      := flyin
DEFAULT_MAP :=maps/easy/01_linear_path.txt
.PHONY: install run debug clean lint 

install:
	$(PIP) install -r requirements.txt


run:
	PYTHONPATH=src $(PYTHON) -m $(MODULE) $(if $(MAP),$(MAP),$(DEFAULT_MAP)) --gui


debug:
	PYTHONPATH=src $(PYTHON) -m pdb -m $(MODULE) $(if $(MAP),$(MAP),$(DEFAULT_MAP))

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 src/flyin
	mypy src/flyin --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs
