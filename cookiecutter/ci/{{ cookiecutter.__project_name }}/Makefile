{%- set src_infix = "src/" if cookiecutter.src_layout else "" %}
{%- if cookiecutter.translations %}
LANGUAGES=de
{%- endif %}
{%- if cookiecutter.glue %}
GLUE_PLUGINS=$(notdir $(wildcard pulp-glue{{ cookiecutter.__app_label_suffix }}/{{ src_infix }}pulp_glue/*))
{%- endif %}
CLI_PLUGINS=$(notdir $(wildcard {{ src_infix }}pulpcore/cli/*))

.PHONY: info
info:
{%- if cookiecutter.glue %}
	@echo Pulp glue
	@echo plugins: $(GLUE_PLUGINS)
{%- endif %}
	@echo Pulp CLI
	@echo plugins: $(CLI_PLUGINS)

.PHONY: build
build:
	uv build --all

.PHONY: _format
_format:
	ruff format
	ruff check --select I --fix

.PHONY: format
format:
	uv run --isolated --group lint $(MAKE) _format

.PHONY: _autofix
_autofix:
	ruff check --fix

.PHONY: autofix
autofix:
	uv lock
	uv run --isolated --group lint $(MAKE) _autofix

.PHONY: _lint
_lint:
	find tests .ci -name '*.sh' -print0 | xargs -0 shellcheck -x
	ruff format --check --diff
	ruff check
{%- if cookiecutter.glue and cookiecutter.app_label %}
	.ci/scripts/check_cli_dependencies.py
{%- endif %}
	.ci/scripts/check_click_for_mypy.py
	mypy
{%- if cookiecutter.glue %}
	cd pulp-glue{{ cookiecutter.__app_label_suffix }}; mypy
{%- endif %}
	@echo "🙊 Code 🙈 LGTM 🙉 !"

.PHONY: lint
lint:
	uv lock --check
	uv run --isolated --group lint $(MAKE) _lint

tests/cli.toml:
	cp $@.example $@
	@echo "In order to configure the tests to talk to your test server, you might need to edit $@ ."

.PHONY: _test
_test: | tests/cli.toml
	pytest -v tests {%- if cookiecutter.glue %} pulp-glue{{ cookiecutter.__app_label_suffix }}/tests {%- endif %}
	{%- if cookiecutter.__app_label_suffix == "" %} cookiecutter/pulp_filter_extension.py {%- endif %}

.PHONY: test
test:
	uv run $(MAKE) _test

.PHONY: _livetest
_livetest: | tests/cli.toml
	pytest -v tests {%- if cookiecutter.glue %} pulp-glue{{ cookiecutter.__app_label_suffix }}/tests {%- endif %} -m live

.PHONY: livetest
livetest:
	uv run $(MAKE) _livetest

.PHONY: _paralleltest
_paralleltest: | tests/cli.toml
	pytest -v tests {%- if cookiecutter.glue %} pulp-glue{{ cookiecutter.__app_label_suffix }}/tests {%- endif %} -m live -n 8

.PHONY: paralleltest
paralleltest:
	uv run $(MAKE) _paralleltest

.PHONY: _unittest
_unittest:
	pytest -v tests {%- if cookiecutter.glue %} pulp-glue{{ cookiecutter.__app_label_suffix }}/tests {%- endif %}
	{%- if cookiecutter.__app_label_suffix == "" %} cookiecutter/pulp_filter_extension.py {%- endif %} -m "not live"

.PHONY: unittest
unittest:
	uv run $(MAKE) _unittest
{%- if cookiecutter.glue %}

.PHONY: _unittest_glue
_unittest_glue:
	pytest -v pulp-glue{{ cookiecutter.__app_label_suffix }}/tests -m "not live"

.PHONY: unittest_glue
unittest_glue:
	uv run $(MAKE) _unittest_glue
{%- endif %}
{%- if cookiecutter.docs %}

.PHONY: docs
docs:
	pulp-docs build

.PHONY: servedocs
servedocs:
	pulp-docs serve -w CHANGES.md -w pulp-glue/pulp_glue -w pulp_cli/generic.py
{%- endif %}
{%- if cookiecutter.translations %}
{%- if cookiecutter.glue %}

pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/%/locale/messages.pot: pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/%/*.py
	xgettext -d $* -o $@ pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/$*/*.py
	sed -i 's/charset=CHARSET/charset=UTF-8/g' $@
{%- endif %}

pulpcore/cli/%/locale/messages.pot: pulpcore/cli/%/*.py
	xgettext -d $* -o $@ pulpcore/cli/$*/*.py
	sed -i 's/charset=CHARSET/charset=UTF-8/g' $@

.PHONY: extract_messages
extract_messages: {%- if cookiecutter.glue %} $(foreach GLUE_PLUGIN,$(GLUE_PLUGINS),pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/$(GLUE_PLUGIN)/locale/messages.pot) {%- endif %} $(foreach CLI_PLUGIN,$(CLI_PLUGINS),pulpcore/cli/$(CLI_PLUGIN)/locale/messages.pot)
{%- if cookiecutter.glue %}

$(foreach LANGUAGE,$(LANGUAGES),pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/%/locale/$(LANGUAGE)/LC_MESSAGES/messages.po): pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/%/locale/messages.pot
	[ -e $(@D) ] || mkdir -p $(@D)
	[ ! -e $@ ] || msgmerge --update $@ $<
	[ -e $@ ] || cp $< $@
{%- endif %}

$(foreach LANGUAGE,$(LANGUAGES),pulpcore/cli/%/locale/$(LANGUAGE)/LC_MESSAGES/messages.po): pulpcore/cli/%/locale/messages.pot
	[ -e $(@D) ] || mkdir -p $(@D)
	[ ! -e $@ ] || msgmerge --update $@ $<
	[ -e $@ ] || cp $< $@

%.mo: %.po
	msgfmt -o $@ $<

.PHONY: compile_messages
compile_messages: {%- if cookiecutter.glue %} $(foreach LANGUAGE,$(LANGUAGES),$(foreach GLUE_PLUGIN,$(GLUE_PLUGINS),pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/$(GLUE_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.mo)) {%- endif %} $(foreach LANGUAGE,$(LANGUAGES),$(foreach CLI_PLUGIN,$(CLI_PLUGINS),pulpcore/cli/$(CLI_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.mo))

{%- endif %}
{%- if cookiecutter.translations %}

.PRECIOUS: {%- if cookiecutter.glue %} $(foreach LANGUAGE,$(LANGUAGES),$(foreach GLUE_PLUGIN,$(GLUE_PLUGINS),pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/$(GLUE_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.po)) {%- endif %} $(foreach LANGUAGE,$(LANGUAGES),$(foreach CLI_PLUGIN,$(CLI_PLUGINS),pulpcore/cli/$(CLI_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.po))
{%- endif %}
