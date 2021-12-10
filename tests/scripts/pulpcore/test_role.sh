#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" --min-version "3.17.0.dev" || exit 3

USERPASS="Yeech6ba"

cleanup() {
  pulp group destroy --name "clitest" || true
  pulp group destroy --name "clitest2" || true
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

expect_succ pulp user role-assignment add --username "clitest" --role "clitest.group_viewer" --object "${GROUP_HREF}"
expect_succ pulp --username clitest --password "${USERPASS}" group show --name "clitest"
expect_succ pulp user role-assignment remove --username "clitest" --role "clitest.group_viewer" --object "${GROUP_HREF}"
expect_fail pulp --username clitest --password "${USERPASS}" group show --name "clitest"

expect_succ pulp group role-assignment add --group "clitest" --role "clitest.group_viewer" --object "${GROUP_HREF}"
expect_succ pulp --username clitest --password "${USERPASS}" group show --name "clitest"
expect_succ pulp group role-assignment remove --group "clitest" --role "clitest.group_viewer" --object "${GROUP_HREF}"
expect_fail pulp --username clitest --password "${USERPASS}" group show --name "clitest"

expect_succ pulp user role-assignment add --username "clitest" --role "core.group_creator" --object ""
expect_succ pulp --username clitest --password "${USERPASS}" group create --name "clitest2"
expect_succ pulp --username clitest --password "${USERPASS}" group role my-permissions --name "clitest2"

expect_succ pulp role destroy --name "clitest.group_viewer"
