black:
	isort .
	black .

lint:
	find . -name '*.sh' -print0 | xargs -0 shellcheck -x
	black --diff --check .
	isort -c --diff .
	flake8
	mypy
	@echo "🙊 Code 🙈 LGTM 🙉 !"

tests/cli.toml:
	cp $@.example $@
	@echo "In order to configure the tests to talk to your test server, you might need to edit $@ ."

test: | tests/cli.toml
	pytest -v tests

servedocs:
	mkdocs serve

site:
	mkdocs build

.PHONY: black lint servedocs
