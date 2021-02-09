black:
	black .

lint:
	find . -name '*.sh' -print0 | xargs -0 shellcheck -x
	black --diff --check .
	isort -c --diff .
	flake8 --config flake8.cfg
	mypy
	@echo "🙊 Code 🙈 LGTM 🙉 !"

tests/settings.toml:
	cp $@.example $@
	@echo "In order to configure the tests to talk to your test server, you might need to edit $@ ."

test: | tests/settings.toml
	pytest -v tests

.PHONY: black lint
