#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp container repository destroy --name "cli_test_container_repository" || true
  pulp container distribution destroy --name "cli_test_container_distro" || true
  pulp container distribution destroy --name "cli_test_container_distro_ver" || true
}
trap cleanup EXIT

expect_succ pulp container repository create --name "cli_test_container_repository"

expect_succ pulp container distribution create --name "cli_test_container_distro" \
  --base-path "cli_test_container_distro" \
  --repository "cli_test_container_repository"

expect_succ pulp container distribution create --name "cli_test_container_distro_ver" \
  --base-path "cli_test_container_distro_ver" \
  --repository "cli_test_container_repository" \
  --version 0

expect_succ pulp container distribution list
expect_succ pulp container distribution show --name "cli_test_container_distro"

expect_succ pulp container distribution destroy --name "cli_test_container_distro"
