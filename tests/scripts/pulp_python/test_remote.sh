#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" --min-version "3.1.0.dev" || exit 3

cleanup() {
  pulp python remote destroy --name "cli_test_python_remote" || true
  pulp python remote destroy --name "cli_test_complex_remote" || true
}
trap cleanup EXIT

expect_succ pulp python remote list

expect_succ pulp python remote create --name "cli_test_python_remote" --url "$PYTHON_REMOTE_URL"
expect_succ pulp python remote show --name "cli_test_python_remote"
expect_succ pulp python remote list

if [ "$(pulp debug has-plugin --name "python" --min-version "3.2.0.dev")" = "true" ]
  then
    expect_succ pulp python remote create --name "cli_test_complex_remote" --url "$PYTHON_REMOTE_URL" --keep-latest-packages 3 --package-types '["sdist", "bdist_wheel"]' --exclude-platforms '["windows"]'
  else
    expect_fail pulp python remote create --name "cli_test_complex_remote" --url "$PYTHON_REMOTE_URL" --keep-latest-packages 3 --package-types '["sdist", "bdist_wheel"]' --exclude-platforms '["windows"]'
fi
expect_succ pulp python remote destroy --name "cli_test_python_remote"
