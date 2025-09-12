#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" --specifier ">=2.11.0" || exit 23

USERPASS="Yeech6ba"

cleanup() {
  pulp group destroy --name "container-role-clitest" || true
  pulp user destroy --username "container-role-clitest" || true
  pulp container repository destroy --name "container-role-clitest" || true
}
trap cleanup EXIT

expect_succ pulp user create --username "container-role-clitest" --password "${USERPASS}"
expect_succ pulp group create --name "container-role-clitest"
expect_succ pulp group user add --group "container-role-clitest" --username "container-role-clitest"

expect_succ pulp -p noauth --username container-role-clitest --password "${USERPASS}" container repository list
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "0"

expect_deny pulp -p noauth --username container-role-clitest --password "${USERPASS}" container repository create --name "container-role-clitest"
expect_succ pulp container repository create --name "container-role-clitest"
REPOSITORY_HREF=$(jq -r '.pulp_href' <<<"${OUTPUT}")
expect_fail pulp -p noauth --username container-role-clitest --password "${USERPASS}" container repository show --repository "container-role-clitest"
expect_fail pulp -p noauth --username container-role-clitest --password "${USERPASS}" container repository show --repository "${REPOSITORY_HREF}"

expect_succ pulp container repository role add --name "container-role-clitest" --user "container-role-clitest" --role "container.containerrepository_viewer"
expect_succ pulp -p noauth --username container-role-clitest --password "${USERPASS}" container repository show --repository "container-role-clitest"
expect_succ pulp -p noauth --username container-role-clitest --password "${USERPASS}" container repository show --repository "${REPOSITORY_HREF}"

expect_deny pulp -p noauth --username container-role-clitest --password "${USERPASS}" container repository update --href "${REPOSITORY_HREF}" --retain-repo-versions 1
