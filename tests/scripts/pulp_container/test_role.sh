#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" --min-version "2.11.0" || exit 3

USERPASS="Yeech6ba"

cleanup() {
  pulp group destroy --name "clitest" || true
  pulp user destroy --username "clitest" || true
  pulp container repository destroy --name "clitest" || true
}
trap cleanup EXIT

expect_succ pulp user create --username "clitest" --password "${USERPASS}"
expect_succ pulp group create --name "clitest"
expect_succ pulp group user add --group "clitest" --username "clitest"

expect_succ pulp --username clitest --password "${USERPASS}" container repository list
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "0"

expect_deny pulp --username clitest --password "${USERPASS}" container repository create --name "clitest"
expect_succ pulp container repository create --name "clitest"
REPOSITORY_HREF=$(jq -r '.pulp_href' <<<"${OUTPUT}")
expect_fail pulp --username clitest --password "${USERPASS}" container repository show --name "clitest"
expect_fail pulp --username clitest --password "${USERPASS}" container repository show --href "${REPOSITORY_HREF}"

expect_succ pulp container repository role add --name "clitest" --user "clitest" --role "container.containerrepository_viewer"
expect_succ pulp --username clitest --password "${USERPASS}" container repository show --name "clitest"
expect_succ pulp --username clitest --password "${USERPASS}" container repository show --href "${REPOSITORY_HREF}"

expect_deny pulp --username clitest --password "${USERPASS}" container repository update --href "${REPOSITORY_HREF}" --retain-repo-versions 1
