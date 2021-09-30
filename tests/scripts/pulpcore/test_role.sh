#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" --min-version "3.17.0.dev" || exit 3

USERPASS="Yeech6ba"

cleanup() {
  pulp group destroy --name "clitest" || true
  pulp user destroy --username "clitest" || true
  pulp role destroy --name "clitest.group_viewer" || true
}
trap cleanup EXIT

expect_succ pulp role list
expect_succ pulp role show --name "core.task_owner"

expect_succ pulp role create --name "clitest.group_viewer" --permission "core.view_group"
expect_succ pulp role show --name "clitest.group_viewer"

expect_succ pulp user create --username "clitest" --password "${USERPASS}"
expect_succ pulp group create --name "clitest"
GROUP_HREF=$(jq -r '.pulp_href' <<<"${OUTPUT}")
expect_succ pulp group user add --group "clitest" --username "clitest"

expect_succ pulp --username clitest --password "${USERPASS}" task list
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "0"

expect_fail pulp -p user group show --name "clitest"

expect_succ pulp user role add --username "clitest" --role "clitest.group_viewer" --object "${GROUP_HREF}"
expect_succ pulp --username clitest --password "${USERPASS}" group show --name "clitest"
expect_succ pulp user role remove --username "clitest" --role "clitest.group_viewer" --object "${GROUP_HREF}"
expect_fail pulp --username clitest --password "${USERPASS}" group show --name "clitest"

expect_succ pulp group role add --group "clitest" --role "clitest.group_viewer" --object "${GROUP_HREF}"
expect_succ pulp --username clitest --password "${USERPASS}" group show --name "clitest"
expect_succ pulp group role remove --group "clitest" --role "clitest.group_viewer" --object "${GROUP_HREF}"
expect_fail pulp --username clitest --password "${USERPASS}" group show --name "clitest"

expect_succ pulp role destroy --name "clitest.group_viewer"
