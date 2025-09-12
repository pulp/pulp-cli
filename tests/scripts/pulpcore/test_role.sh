#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

USERPASS="Yeech6ba"

cleanup() {
  pulp group destroy --name "core-role-clitest" || true
  pulp group destroy --name "core-role-clitest2" || true
  pulp user destroy --username "core-role-clitest" || true
  pulp role destroy --name "core-role-clitest.group_viewer" || true
}
trap cleanup EXIT

expect_succ pulp role list
expect_succ pulp role show --name "core.task_owner"

expect_succ pulp role create --name "core-role-clitest.group_viewer" --permission "core.view_group"
expect_succ pulp role show --name "core-role-clitest.group_viewer"

expect_succ pulp user create --username "core-role-clitest" --password "${USERPASS}"
expect_succ pulp group create --name "core-role-clitest"
GROUP_HREF=$(jq -r '.pulp_href' <<<"${OUTPUT}")
expect_succ pulp group user add --group "core-role-clitest" --username "core-role-clitest"

expect_succ pulp -p noauth --username core-role-clitest --password "${USERPASS}" task list
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "0"

expect_fail pulp -p noauth --username core-role-clitest --password "${USERPASS}" group show --name "core-role-clitest"

expect_succ pulp user role-assignment add --username "core-role-clitest" --role "core-role-clitest.group_viewer" --object "${GROUP_HREF}"
expect_succ pulp user role-assignment list --username "core-role-clitest" --role "core-role-clitest.group_viewer" --object "${GROUP_HREF}"
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "1"
expect_succ pulp user role-assignment list --username "core-role-clitest" --role-in "core-role-clitest.group_viewer" --object "${GROUP_HREF}"
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "1"
expect_succ pulp -p noauth --username core-role-clitest --password "${USERPASS}" group show --name "core-role-clitest"
expect_succ pulp user role-assignment remove --username "core-role-clitest" --role "core-role-clitest.group_viewer" --object "${GROUP_HREF}"
expect_fail pulp -p noauth --username core-role-clitest --password "${USERPASS}" group show --name "core-role-clitest"

expect_succ pulp group role-assignment add --group "core-role-clitest" --role "core-role-clitest.group_viewer" --object "${GROUP_HREF}"
expect_succ pulp group role-assignment list --group "core-role-clitest" --role "core-role-clitest.group_viewer" --object "${GROUP_HREF}"
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "1"
expect_succ pulp group role-assignment list --group "core-role-clitest" --role-in "core-role-clitest.group_viewer" --object "${GROUP_HREF}"
test "$(echo "${OUTPUT}" | jq -r 'length' )" = "1"
expect_succ pulp -p noauth --username core-role-clitest --password "${USERPASS}" group show --name "core-role-clitest"
expect_succ pulp group role-assignment remove --group "core-role-clitest" --role "core-role-clitest.group_viewer" --object "${GROUP_HREF}"
expect_fail pulp -p noauth --username core-role-clitest --password "${USERPASS}" group show --name "core-role-clitest"

expect_succ pulp user role-assignment add --username "core-role-clitest" --role "core.group_creator" --object ""
expect_succ pulp -p noauth --username core-role-clitest --password "${USERPASS}" group create --name "core-role-clitest2"
expect_succ pulp -p noauth --username core-role-clitest --password "${USERPASS}" group role my-permissions --name "core-role-clitest2"

expect_succ pulp role destroy --name "core-role-clitest.group_viewer"
