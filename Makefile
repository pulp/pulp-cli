black:
	black .

lint:
	find . -name '*.sh' -print0 | xargs -0 shellcheck -x
	black --diff --check .
	flake8 --config flake8.cfg
	mypy

tests/scripts/config/pulp/settings.toml:
	cp $@.example $@

test: | tests/scripts/config/pulp/settings.toml
	pytest -v tests

.PHONY: black lint
