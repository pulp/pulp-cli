{%- if cookiecutter.translations %}
LANGUAGES=de
{%- endif %}
{%- if cookiecutter.glue %}
GLUE_PLUGINS=$(notdir $(wildcard pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/*))
{%- endif %}
CLI_PLUGINS=$(notdir $(wildcard pulpcore/cli/*))

info:
{%- if cookiecutter.glue %}
	@echo Pulp glue
	@echo plugins: $(GLUE_PLUGINS)
{%- endif %}
	@echo Pulp CLI
	@echo plugins: $(CLI_PLUGINS)

build:
{%- if cookiecutter.glue %}
	cd pulp-glue{{ cookiecutter.__app_label_suffix }}; pyproject-build -n
{%- endif %}
	pyproject-build -n

black: format

format:
	isort .
{%- if cookiecutter.glue %}
	cd pulp-glue{{ cookiecutter.__app_label_suffix }}; isort .
{%- endif %}
	black .

lint:
	find tests .ci -name '*.sh' -print0 | xargs -0 shellcheck -x
	isort -c --diff .
{%- if cookiecutter.glue %}
	cd pulp-glue{{ cookiecutter.__app_label_suffix }}; isort -c --diff .
{%- endif %}
	black --diff --check .
	flake8
{%- if cookiecutter.glue and cookiecutter.app_label %}
	.ci/scripts/check_cli_dependencies.py
{%- endif %}
	.ci/scripts/check_click_for_mypy.py
{%- if cookiecutter.glue %}
	MYPYPATH=pulp-glue{{ cookiecutter.__app_label_suffix }} mypy
	cd pulp-glue{{ cookiecutter.__app_label_suffix }}; mypy
{%- else %}
	mypy
{%- endif %}
	@echo "🙊 Code 🙈 LGTM 🙉 !"

tests/cli.toml:
	cp $@.example $@
	@echo "In order to configure the tests to talk to your test server, you might need to edit $@ ."

test: | tests/cli.toml
	python3 -m pytest -v tests {%- if cookiecutter.glue %} pulp-glue{{ cookiecutter.__app_label_suffix }}/tests {%- endif %}
	{%- if cookiecutter.__app_label_suffix == "" %} cookiecutter/pulp_filter_extension.py {%- endif %}

livetest: | tests/cli.toml
	python3 -m pytest -v tests {%- if cookiecutter.glue %} pulp-glue{{ cookiecutter.__app_label_suffix }}/tests {%- endif %} -m live

paralleltest: | tests/cli.toml
	python3 -m pytest -v tests {%- if cookiecutter.glue %} pulp-glue{{ cookiecutter.__app_label_suffix }}/tests {%- endif %} -m live -n 8

unittest:
	python3 -m pytest -v tests {%- if cookiecutter.glue %} pulp-glue{{ cookiecutter.__app_label_suffix }}/tests {%- endif %}
	{%- if cookiecutter.__app_label_suffix == "" %} cookiecutter/pulp_filter_extension.py {%- endif %} -m "not live"
{%- if cookiecutter.glue %}

unittest_glue:
	python3 -m pytest -v pulp-glue{{ cookiecutter.__app_label_suffix }}/tests -m "not live"
{%- endif %}
{%- if cookiecutter.docs %}

docs:
	pulp-docs build

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

compile_messages: {%- if cookiecutter.glue %} $(foreach LANGUAGE,$(LANGUAGES),$(foreach GLUE_PLUGIN,$(GLUE_PLUGINS),pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/$(GLUE_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.mo)) {%- endif %} $(foreach LANGUAGE,$(LANGUAGES),$(foreach CLI_PLUGIN,$(CLI_PLUGINS),pulpcore/cli/$(CLI_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.mo))

{%- endif %}
.PHONY: build info black lint test {%- if cookiecutter.docs %} docs servedocs {%- endif %}
{%- if cookiecutter.translations %}
.PRECIOUS: {%- if cookiecutter.glue %} $(foreach LANGUAGE,$(LANGUAGES),$(foreach GLUE_PLUGIN,$(GLUE_PLUGINS),pulp-glue{{ cookiecutter.__app_label_suffix }}/pulp_glue/$(GLUE_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.po)) {%- endif %} $(foreach LANGUAGE,$(LANGUAGES),$(foreach CLI_PLUGIN,$(CLI_PLUGINS),pulpcore/cli/$(CLI_PLUGIN)/locale/$(LANGUAGE)/LC_MESSAGES/messages.po))
{%- endif %}
