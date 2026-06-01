LANGUAGES := "de"
GLUE_PLUGINS := `ls pulp-glue/src/pulp_glue/ | tr '\n' ' '`
CLI_PLUGINS := `ls src/pulpcore/cli/ | tr '\n' ' '`

# Show discovered plugins
info:
    @echo "Pulp glue"
    @echo "plugins: {{ GLUE_PLUGINS }}"
    @echo "Pulp CLI"
    @echo "plugins: {{ CLI_PLUGINS }}"

# Build all packages
[group('build')]
build:
    uv build --all

# Format code and sort imports
[group('lint')]
format:
    #!/usr/bin/env -S uv run --isolated --group lint bash
    set -euxo pipefail
    ruff format
    ruff check --select I --fix

# Auto-fix lint violations
[group('lint')]
autofix:
    #!/usr/bin/env -S uv run --isolated --group lint bash
    set -euxo pipefail
    uv lock
    ruff check --fix

# Run all linters
[group('lint')]
lint:
    #!/usr/bin/env -S uv run --isolated --group lint bash
    set -euxo pipefail
    uv lock --check
    find tests .ci -name '*.sh' -print0 | xargs -0 shellcheck -x
    ruff format --check --diff
    ruff check
    .ci/scripts/check_click_for_mypy.py
    mypy
    cd pulp-glue && mypy
    echo "🙊 Code 🙈 LGTM 🙉 !"

[private]
[no-exit-message]
setup-test-config:
    #!/usr/bin/env bash
    if [ ! -f tests/cli.toml ]; then
        cp tests/cli.toml.example tests/cli.toml
        echo "In order to configure the tests to talk to your test server, you might need to edit tests/cli.toml ."
    fi

# Run all tests
[group('test')]
test: setup-test-config
    uv run pytest -v tests pulp-glue/tests cookiecutter/pulp_filter_extension.py

# Run live tests against a running server
[group('test')]
livetest: setup-test-config
    uv run pytest -v tests pulp-glue/tests -m live

# Run live tests in parallel
[group('test')]
paralleltest: setup-test-config
    uv run pytest -v tests pulp-glue/tests -m live -n 8

# Run unit tests only (no server required)
[group('test')]
unittest:
    uv run pytest -v tests pulp-glue/tests cookiecutter/pulp_filter_extension.py -m "not live"

# Run glue unit tests only
[group('test')]
unittest-glue:
    uv run pytest -v pulp-glue/tests -m "not live"

# Build documentation
[group('docs')]
docs:
    pulp-docs build

# Serve documentation with live reload
[group('docs')]
servedocs:
    pulp-docs serve -w CHANGES.md -w pulp-glue/pulp_glue -w pulp_cli/generic.py

# Extract translatable strings into .pot files
[group('i18n')]
extract-messages:
    #!/usr/bin/env bash
    set -euxo pipefail
    for base in pulp-glue/pulp_glue pulpcore/cli; do
        for dir in "$base"/*/; do
            plugin=$(basename "$dir")
            xgettext -d "$plugin" -o "$dir/locale/messages.pot" "$dir"/*.py
            sed -i 's/charset=CHARSET/charset=UTF-8/g' "$dir/locale/messages.pot"
        done
    done

# Compile .po files into .mo files
[group('i18n')]
compile-messages:
    #!/usr/bin/env bash
    set -euxo pipefail
    for base in pulp-glue/pulp_glue pulpcore/cli; do
        for dir in "$base"/*/; do
            plugin=$(basename "$dir")
            for lang in {{ LANGUAGES }}; do
                potfile="$dir/locale/messages.pot"
                pofile="$dir/locale/$lang/LC_MESSAGES/messages.po"
                mofile="$dir/locale/$lang/LC_MESSAGES/messages.mo"
                mkdir -p "$(dirname "$pofile")"
                if [ -f "$pofile" ]; then
                    msgmerge --update "$pofile" "$potfile"
                else
                    cp "$potfile" "$pofile"
                fi
                msgfmt -o "$mofile" "$pofile"
            done
        done
    done
