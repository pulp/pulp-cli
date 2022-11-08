#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" --min-version "1.11.0" || exit 3

USERPASS="Yeech6ba"

cleanup() {
  pulp user destroy --username "clitest" || true
  pulp file repository destroy --name "clitest" || true
}
trap cleanup EXIT

pulp user create --username "clitest" --password "${USERPASS}"

expect_succ pulp --username clitest --password "${USERPASS}" file repository list
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "0"

expect_deny pulp --username clitest --password "${USERPASS}" file repository create --name "clitest"
expect_succ pulp file repository create --name "clitest"
REPOSITORY_HREF=$(jq -r '.pulp_href' <<<"${OUTPUT}")
expect_fail pulp --username clitest --password "${USERPASS}" file repository show --repository "clitest"
expect_fail pulp --username clitest --password "${USERPASS}" file repository show --href "${REPOSITORY_HREF}"

expect_succ pulp file repository role add --repository "clitest" --user "clitest" --role "file.filerepository_viewer"
expect_succ pulp --username clitest --password "${USERPASS}" file repository show --repository "clitest"
expect_succ pulp --username clitest --password "${USERPASS}" file repository show --href "${REPOSITORY_HREF}"

expect_deny pulp --username clitest --password "${USERPASS}" file repository update --repository "${REPOSITORY_HREF}" --retain-repo-versions 1

expect_succ pulp file repository role remove --name "clitest" --user "clitest" --role "file.filerepository_viewer"
expect_fail pulp --username clitest --password "${USERPASS}" file repository show --repository "clitest"
expect_fail pulp --username clitest --password "${USERPASS}" file repository show --repository "${REPOSITORY_HREF}"
