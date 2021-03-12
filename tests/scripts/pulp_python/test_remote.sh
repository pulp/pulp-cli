#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" --min-version "3.1.0.dev" || exit 3

cleanup() {
  pulp python remote destroy --name "cli_test_python_remote" || true
}
trap cleanup EXIT

expect_succ pulp python remote list

expect_succ pulp python remote create --name "cli_test_python_remote" --url "$PYTHON_REMOTE_URL"
expect_succ pulp python remote show --name "cli_test_python_remote"
expect_succ pulp python remote list
expect_succ pulp python remote destroy --name "cli_test_python_remote"
