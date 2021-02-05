black:
	black .

lint:
	find . -name '*.sh' -print0 | xargs -0 shellcheck -x
	black --diff --check .
	isort -c --diff .
	flake8 --config flake8.cfg
	mypy
	@echo "🙊 Code 🙈 LGTM 🙉 !"

tests/scripts/config/pulp/settings.toml:
	cp $@.example $@

test: | tests/scripts/config/pulp/settings.toml
	pytest -v tests

.PHONY: black lint
