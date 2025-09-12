#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "ansible" || exit 23

cleanup() {
  pulp ansible repository destroy --name "cli_test_ansible_distribution_repository" || true
  pulp ansible distribution destroy --name "cli_test_ansible_distro" || true
  pulp ansible distribution destroy --name "cli_test_ansible_ver_distro" || true
}
trap cleanup EXIT

expect_succ pulp ansible repository create --name "cli_test_ansible_distribution_repository"

expect_succ pulp ansible distribution create --name "cli_test_ansible_distro" \
  --base-path "cli_test_ansible_distro" \
  --repository "cli_test_ansible_distribution_repository"

expect_succ pulp ansible distribution create --name "cli_test_ansible_ver_distro" \
  --base-path "cli_test_ansible_ver_distro" \
  --repository "cli_test_ansible_distribution_repository" \
  --version "0"

expect_succ pulp ansible distribution list
expect_succ pulp ansible distribution show --distribution "cli_test_ansible_distro"
expect_succ pulp ansible distribution update --distribution "cli_test_ansible_distro" --repository ""

expect_succ pulp ansible distribution label set --distribution "cli_test_ansible_distro" --key "test" --value "success"
expect_succ pulp ansible distribution destroy --distribution "cli_test_ansible_distro"
