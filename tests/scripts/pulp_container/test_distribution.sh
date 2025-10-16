#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 23

cleanup() {
  pulp container repository destroy --name "cli_test_container_distribution_repository" || true
  pulp container distribution destroy --name "cli_test_container_distro" || true
  pulp container distribution destroy --name "cli_test_container_distro_ver" || true
}
trap cleanup EXIT

expect_succ pulp container repository create --name "cli_test_container_distribution_repository"

expect_succ pulp container distribution create --name "cli_test_container_distro" \
  --base-path "cli_test_container_distro" \
  --repository "cli_test_container_distribution_repository"

expect_succ pulp container distribution create --name "cli_test_container_distro_ver" \
  --base-path "cli_test_container_distro_ver" \
  --repository "cli_test_container_distribution_repository" \
  --version 0

expect_succ pulp container distribution list
expect_succ pulp container distribution show --distribution "cli_test_container_distro"

# see https://pulp.plan.io/issues/9497
if pulp debug has-plugin --name "container" --specifier ">=2.10.0"

then
  expect_succ pulp container distribution update --distribution "cli_test_container_distro" --version 0
  expect_succ pulp container distribution update --distribution "cli_test_container_distro" --repository ""
  expect_succ pulp container distribution update --distribution "cli_test_container_distro_ver" --repository "cli_test_container_distribution_repository"
  expect_succ pulp container distribution update --distribution "cli_test_container_distro_ver" --repository ""
fi
expect_succ pulp container distribution destroy --distribution "cli_test_container_distro"
