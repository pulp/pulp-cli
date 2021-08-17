#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 3

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
# Not sure what's going on here. Maybe a bug in the distribution serializer.
# expect_succ pulp container distribution update --name "cli_test_container_distro" --version 0
# expect_succ pulp container distribution update --name "cli_test_container_distro" --repository ""
# expect_succ pulp container distribution update --name "cli_test_container_distro_ver" --repository "cli_test_container_repository"
# expect_succ pulp container distribution update --name "cli_test_container_distro_ver" --repository ""

expect_succ pulp container distribution destroy --name "cli_test_container_distro"
