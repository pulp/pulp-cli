#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" --min-version "3.17.0" || exit 3


cleanup() {
  pulp rpm repository destroy --name "cli_test_rpm_repository" || true
}
trap cleanup EXIT
SMALLCOMPS="$(dirname "$(realpath "$0")")"/comps.xml
LARGECOMPS="$(dirname "$(realpath "$0")")"/centos8-base-comps.xml

if pulp debug has-plugin --name "rpm" --min-version "3.16.0"
then
  expect_succ pulp rpm repository create --name "cli_test_rpm_repository"
  repo_href="$(echo "$OUTPUT" | jq -r ".pulp_href")"
  expect_succ pulp rpm comps-upload --file "${SMALLCOMPS}"
  test "$(echo "$OUTPUT" | jq -r '.created_resources | length')" = 4  # just comps-units
  expect_succ pulp rpm comps-upload --file "${SMALLCOMPS}"  --repository "${repo_href}"
  test "$(echo "$OUTPUT" | jq -r '.created_resources | length')" = 5  # comps-units plus repo-version
  expect_succ pulp rpm comps-upload --file "${LARGECOMPS}"  --repository "cli_test_rpm_repository"
  test "$(echo "$OUTPUT" | jq -r '.created_resources | length')" = 43  # units + version
  expect_succ pulp rpm comps-upload --file "${SMALLCOMPS}"  --repository "cli_test_rpm_repository"
  test "$(echo "$OUTPUT" | jq -r '.created_resources | length')" = 4  # just units (already there, no vers created)
  expect_succ pulp rpm comps-upload --file "${SMALLCOMPS}"  --repository "cli_test_rpm_repository" --replace True
  test "$(echo "$OUTPUT" | jq -r '.created_resources | length')" = 5  # units+version
fi
