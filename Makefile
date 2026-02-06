
LANGUAGES=de
GLUE_PLUGINS=$(notdir $(wildcard pulp-glue/src/pulp_glue/*))
CLI_PLUGINS=$(notdir $(wildcard src/pulpcore/cli/*))

.PHONY: info
info:
	@echo Pulp glue
	@echo plugins: $(GLUE_PLUGINS)
	@echo Pulp CLI
	@echo plugins: $(CLI_PLUGINS)

.PHONY: build
build:
	uv build --all

.PHONY: format
format:
	ruff format
	ruff check --fix

.PHONY: uv-format
uv-format:
	uv lock
	uv run --isolated --group lint $(MAKE) format

.PHONY: lint
lint:
	find tests .ci -name '*.sh' -print0 | xargs -0 shellcheck -x
	ruff format --check --diff
	ruff check --diff
	.ci/scripts/check_click_for_mypy.py
	mypy
	cd pulp-glue; mypy
	@echo "🙊 Code 🙈 LGTM 🙉 !"

.PHONY: uv-lint
uv-lint:
	uv lock --check
	uv run --isolated --group lint $(MAKE) lint

tests/cli.toml:
	cp $@.example $@
	@echo "In order to configure the tests to talk to your test server, you might need to edit $@ ."

.PHONY: test
test: | tests/cli.toml
	python3 -m pytest -v tests pulp-glue/tests cookiecutter/pulp_filter_extension.py

.PHONY: livetest
livetest: | tests/cli.toml
	python3 -m pytest -v tests pulp-glue/tests -m live

.PHONY: paralleltest
paralleltest: | tests/cli.toml
	python3 -m pytest -v tests pulp-glue/tests -m live -n 8

.PHONY: unittest
unittest:
	python3 -m pytest -v tests pulp-glue/tests cookiecutter/pulp_filter_extension.py -m "not live"

.PHONY: unittest_glue
unittest_glue:
	python3 -m pytest -v pulp-glue/tests -m "not live"

.PHONY: docs
docs:
	pulp-docs build

.PHONY: servedocs
servedocs:
	pulp-docs serve -w CHANGES.md -w pulp-glue/pulp_glue -w pulp_cli/generic.py

pulp-glue/pulp_glue/%/locale/messages.pot: pulp-glue/pulp_glue/%/*.py
	xgettext -d $* -o $@ pulp-glue/pulp_glue/$*/*.py
	sed -i 's/charset=CHARSET/charset=UTF-8/g' $@

pulpcore/cli/%/locale/messages.pot: pulpcore/cli/%/*.py
	xgettext -d $* -o $@ pulpcore/cli/$*/*.py
	sed -i 's/charset=CHARSET/charset=UTF-8/g' $@

.PHONY: extract_messages
extract_messages: $(foreach GLUE_PLUGIN,$(GLUE_PLUGINS),pulp-glue/pulp_glue/$(GLUE_PLUGIN)/locale/messages.pot) $(foreach CLI_PLUGIN,$(CLI_PLUGINS),pulpcore/cli/$(CLI_PLUGIN)/locale/messages.pot)

$(foreach LANGUAGE,$(LANGUAGES),pulp-glue/pulp_glue/%/locale/$(LANGUAGE)/LC_MESSAGES/messages.po): pulp-glue/pulp_glue/%/locale/messages.pot
	[ -e $(@D) ] || mkdir -p $(@D)
	[ ! -e $@ ] || msgmerge --update $@ $<
	[ -e $@ ] || cp $< $@

$(foreach LANGUAGE,$(LANGUAGES),pulpcore/cli/%/locale/$(LANGUAGE)/LC_MESSAGES/messages.po): pulpcore/cli/%/locale/messages.pot
	[ -e $(@D) ] || mkdir -p $(@D)
	[ ! -e $@ ] || msgmerge --update $@ $<
	[ -e $@ ] || cp $< $@

%.mo: %.po
	msgfmt -o $@ $<

.PHONY: compile_messages
compile_messages: $(foreach LANGUAGE,$(LANGUAGES),$(foreach GLUE_PLUGIN,$(GLUE_PLUGINS),pulp-glue/pulp_glue/$(GLUE_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.mo)) $(foreach LANGUAGE,$(LANGUAGES),$(foreach CLI_PLUGIN,$(CLI_PLUGINS),pulpcore/cli/$(CLI_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.mo))

.PRECIOUS: $(foreach LANGUAGE,$(LANGUAGES),$(foreach GLUE_PLUGIN,$(GLUE_PLUGINS),pulp-glue/pulp_glue/$(GLUE_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.po)) $(foreach LANGUAGE,$(LANGUAGES),$(foreach CLI_PLUGIN,$(CLI_PLUGINS),pulpcore/cli/$(CLI_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.po))
