PY ?= python3

.PHONY: check test validate strict baseline build browser

check: test validate        ## everything that must pass before a commit
	$(PY) -m py_compile kb/*.py gen/*.py
	@echo "check: OK"

test:                       ## generator, validator and walk-tool tests
	$(PY) -m unittest discover -s gen/tests
	$(PY) -m unittest discover -s kb/tests

validate:                   ## ratchet: no rule may get worse than the baseline
	$(PY) kb/validate_site.py --site docs

strict:                     ## show every violation, ignore the baseline
	$(PY) kb/validate_site.py --site docs --strict

baseline:                   ## accept today's counts (only after they went down)
	$(PY) kb/validate_site.py --site docs --update-baseline

build:                      ## regenerate docs/ then validate it
	$(PY) gen/build.py
	$(PY) kb/validate_site.py --site docs

browser:                    ## needs: npm install jsdom
	node gen/tests/browser_test.js docs
