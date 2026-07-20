.DEFAULT_GOAL := help
.PHONY: help doctor test test-public figures figures-python figures-r molecular interactive manuscript docs publication reproduce reproduce-full access-diagnostics nexus-bell-dry-run all-public

LINT_TARGETS := scripts/test_quantinuum_access.py scripts/submit_hosted_pauli_energy.py scripts/reproduce_everything.py tests

help:
	@echo "DHFR InQuanto Resistance — safe repository commands"
	@echo ""
	@echo "  make doctor              Show the active Python and key tool availability"
	@echo "  make reproduce           Rebuild and verify all standard public assets"
	@echo "  make reproduce-full      Public assets plus optional R figures and manuscript"
	@echo "  make test-public         Compile, lint, and run public tests"
	@echo "  make publication         Rebuild Python publication assets and molecular render"
	@echo "  make figures             Rebuild Python figures, tables, and manifests"
	@echo "  make figures-r           Rebuild optional R figures"
	@echo "  make molecular           Rebuild the WT_TMP molecular render"
	@echo "  make manuscript          Build the optional manuscript PDF"
	@echo "  make access-diagnostics  Inspect local Quantinuum access configuration"
	@echo "  make nexus-bell-dry-run  Preview the guarded Nexus Bell path without submitting"
	@echo ""
	@echo "All standard reproduction targets are local and do not submit provider jobs."

doctor:
	@python --version
	@python -c "import sys; print('Python executable:', sys.executable)"
	@python -c "import importlib.util as u; print('pytest:', bool(u.find_spec('pytest'))); print('ruff:', bool(u.find_spec('ruff'))); print('numpy:', bool(u.find_spec('numpy'))); print('pandas:', bool(u.find_spec('pandas')))"
	@command -v Rscript >/dev/null 2>&1 && echo "Rscript: available" || echo "Rscript: optional, not found"

test test-public:
	python -m compileall -q scripts
	ruff check $(LINT_TARGETS)
	pytest -q

figures figures-python:
	python scripts/build_publication_assets.py

figures-r:
	Rscript analysis/R/make_publication_figures.R

molecular:
	python scripts/render_molecular_3d.py

interactive:
	@echo "Static interactive files are under visualization/interactive and docs/site."

manuscript:
	cd manuscript && ./build.sh

docs:
	@echo "Static site files are under docs/site/."

publication: figures molecular

reproduce:
	python scripts/reproduce_everything.py

reproduce-full:
	python scripts/reproduce_everything.py --include-r --include-manuscript

access-diagnostics:
	python scripts/diagnose_quantinuum_access.py

nexus-bell-dry-run:
	python scripts/test_quantinuum_access.py --nexus-emulator --backend H2-1SC --dry-run

all-public: reproduce
