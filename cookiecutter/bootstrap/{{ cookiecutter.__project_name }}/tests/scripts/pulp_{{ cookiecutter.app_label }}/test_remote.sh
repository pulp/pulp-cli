#!/bin/bash

set -eu

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")/config.source"

ENTITIES_NAME="test_{{ cookiecutter.app_label }}_remote"

cleanup() {
  pulp {{ cookiecutter.app_label }} remote destroy --name "${ENTITIES_NAME}" || true
}
trap cleanup EXIT

# Fail to create some remotes:
expect_fail pulp {{ cookiecutter.app_label }} remote create --name "foo"

# Create and a remote:
expect_succ pulp {{ cookiecutter.app_label }} remote create --name "foo" --url "foo"
