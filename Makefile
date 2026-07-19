.DEFAULT_GOAL := help
.PHONY: help test test-public figures figures-python figures-r molecular interactive manuscript docs publication access-diagnostics local-bell-test all-public
help:
	@echo "Safe public targets: test, figures, molecular, docs, publication, access-diagnostics, local-bell-test"
test test-public:
	python -m compileall -q scripts
	ruff check scripts tests
	pytest -q
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
local-bell-test:
	python scripts/test_quantinuum_access.py --local-emulator
all-public: publication test-public
