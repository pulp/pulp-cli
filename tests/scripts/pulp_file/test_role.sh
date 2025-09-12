#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" --specifier ">=1.11.0" || exit 23

USERPASS="Yeech6ba"

cleanup() {
  pulp user destroy --username "file-role-clitest" || true
  pulp file repository destroy --name "file-role-clitest" || true
}
trap cleanup EXIT

pulp user create --username "file-role-clitest" --password "${USERPASS}"

expect_succ pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository list
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "0"

expect_deny pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository create --name "file-role-clitest"
expect_succ pulp file repository create --name "file-role-clitest"
REPOSITORY_HREF=$(jq -r '.pulp_href' <<<"${OUTPUT}")
expect_fail pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository show --repository "file-role-clitest"
expect_fail pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository show --href "${REPOSITORY_HREF}"

expect_succ pulp file repository role add --repository "file-role-clitest" --user "file-role-clitest" --role "file.filerepository_viewer"
expect_succ pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository show --repository "file-role-clitest"
expect_succ pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository show --href "${REPOSITORY_HREF}"

expect_deny pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository update --repository "${REPOSITORY_HREF}" --retain-repo-versions 1

expect_succ pulp file repository role remove --name "file-role-clitest" --user "file-role-clitest" --role "file.filerepository_viewer"
expect_fail pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository show --repository "file-role-clitest"
expect_fail pulp -p noauth --username file-role-clitest --password "${USERPASS}" file repository show --repository "${REPOSITORY_HREF}"
