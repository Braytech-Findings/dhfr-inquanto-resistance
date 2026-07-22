.DEFAULT_GOAL := help
.PHONY: help setup test test-public validate figures figures-python figures-r molecular interactive manuscript docs publication access-diagnostics nexus-bell-dry-run all-public
help:
	@echo "Safe public targets: setup, test, validate, figures, molecular, docs, publication, access-diagnostics, nexus-bell-dry-run"
setup:
	conda env create -f environment.yml
test test-public:
	python -m compileall -q scripts
	ruff check scripts/test_quantinuum_access.py scripts/submit_hosted_pauli_energy.py tests
	pytest -q
validate:
	python scripts/validate_repository.py
figures figures-python:
	python scripts/build_publication_assets.py
figures-r:
	Rscript analysis/R/make_publication_figures.R
molecular:
	python scripts/render_molecular_3d.py
interactive:
	@echo "Static files are under visualization/interactive and docs/site."
manuscript:
	cd manuscript && ./build.sh
docs:
	@echo "Static site is in docs/site/."
publication: figures molecular
access-diagnostics:
	python scripts/diagnose_quantinuum_access.py
nexus-bell-dry-run:
	python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-Emulator --dry-run
all-public: publication test-public
