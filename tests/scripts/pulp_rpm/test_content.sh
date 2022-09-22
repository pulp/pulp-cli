#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" || exit 3

TEST_ADVISORY="$(dirname "$(realpath "$0")")"/test_advisory.json
RPM_FILENAME="lemon-0-1.noarch.rpm"
RPM2_FILENAME="icecubes-2-3.noarch.rpm"
RPM_NAME="lemon"
RPM2_NAME="icecubes"
REPO1_NAME="cli_test_rpm"
REPO2_NAME="cli_test_modular"
PACKAGE_HREF=
ADVISORY_HREF=
cleanup() {
  pulp rpm repository destroy --name "${REPO1_NAME}" || true
  pulp rpm repository destroy --name "${REPO2_NAME}" || true
  pulp rpm remote destroy --name "${REPO1_NAME}" || true
  pulp rpm remote destroy --name "${REPO2_NAME}" || true
  # clean up everything else "asap"
  pulp orphan cleanup --protection-time 0 || true
}
trap cleanup EXIT
cleanup

# Test rpm package upload
wget --no-check-certificate "${RPM_WEAK_DEPS_URL}/${RPM_FILENAME}"
expect_succ pulp rpm content upload --file "${RPM_FILENAME}" --relative-path "${RPM_FILENAME}"
PACKAGE_HREF=$(echo "${OUTPUT}" | jq -r .pulp_href)
expect_succ pulp rpm content show --href "${PACKAGE_HREF}"

expect_succ pulp rpm remote create --name "${REPO1_NAME}" --url "$RPM_REMOTE_URL"
expect_succ pulp rpm remote show --name "${REPO1_NAME}"
expect_succ pulp rpm repository create --name "${REPO1_NAME}" --remote "${REPO1_NAME}"
expect_succ pulp rpm repository show --name "${REPO1_NAME}"

expect_succ pulp rpm repository content modify \
--repository "${REPO1_NAME}" \
--add-content "[{\"pulp_href\": \"${PACKAGE_HREF}\"}]"
expect_succ pulp rpm repository content list --repository "${REPO1_NAME}"
test "$(echo "${OUTPUT}" | jq -r '.[0].pulp_href')" = "${PACKAGE_HREF}"

expect_succ pulp rpm repository content modify \
--repository "${REPO1_NAME}" \
--remove-content "[{\"pulp_href\": \"${PACKAGE_HREF}\"}]"
expect_succ pulp rpm repository content list --repository "${REPO1_NAME}"
test "$(echo "${OUTPUT}" | jq -r length)" -eq "0"

expect_succ pulp rpm repository content add \
--repository "${REPO1_NAME}" \
--package-href "${PACKAGE_HREF}"
expect_succ pulp rpm repository content list --repository "${REPO1_NAME}"
test "$(echo "${OUTPUT}" | jq -r '.[0].pulp_href')" = "${PACKAGE_HREF}"

expect_succ pulp rpm repository content remove \
--repository "${REPO1_NAME}" \
--package-href "${PACKAGE_HREF}"
expect_succ pulp rpm repository content list --repository "${REPO1_NAME}"
test "$(echo "${OUTPUT}" | jq -r length)" -eq "0"

expect_succ pulp rpm repository content modify \
--repository "${REPO1_NAME}" \
--remove-content "[{\"pulp_href\": \"${PACKAGE_HREF}\"}]"

wget --no-check-certificate "${RPM_WEAK_DEPS_URL}/${RPM2_FILENAME}"
expect_succ pulp rpm content upload --file "${RPM2_FILENAME}" --relative-path "${RPM2_FILENAME}" --repository "${REPO1_NAME}"
expect_succ pulp rpm repository content list --repository "${REPO1_NAME}"
test "$(echo "${OUTPUT}" | jq -r length)" -eq "1"

# Test list commands with synced repository

expect_succ pulp rpm remote create --name "${REPO2_NAME}" --url "$RPM_MODULES_REMOTE_URL"
expect_succ pulp rpm repository create --name "${REPO2_NAME}" --remote "${REPO2_NAME}"
expect_succ pulp rpm repository sync --name "${REPO2_NAME}"
VERSION_HREF=$(pulp rpm repository version show --repository "${REPO2_NAME}" | jq -r .pulp_href)

# test list and show for all types
for t in package advisory distribution_tree modulemd_defaults modulemd package_category package_environment package_group package_langpack repo_metadata_file
do
  expect_succ pulp rpm content -t ${t} list --limit 100 --repository-version "${VERSION_HREF}"
  FOUND=$(echo "${OUTPUT}" | jq -r length)
  case ${t} in
    package)
      test "${FOUND}" -eq "35"
      ;;
    advisory)
      test "${FOUND}" -eq "6"
      ;;
    distribution_tree)
      test "${FOUND}" -eq "0"
      ;;
    modulemd_defaults)
      test "${FOUND}" -eq "3"
      ;;
    modulemd)
      test "${FOUND}" -eq "10"
      ;;
    package_category)
      test "${FOUND}" -eq "1"
      ;;
    package_environment)
      test "${FOUND}" -eq "0"
      ;;
    package_group)
      test "${FOUND}" -eq "2"
      ;;
    package_langpack)
      test "${FOUND}" -eq "1"
      ;;
    repo_metadata_file)
      test "${FOUND}" -eq "0"
      ;;
    *)
      ;;
  esac
  if test "${FOUND}" -gt "0"
  then
    ENTITY_HREF=$(echo "${OUTPUT}" | jq -r '.[0] | .pulp_href')
    expect_succ pulp rpm content -t ${t} show --href "${ENTITY_HREF}"
  fi
done

expect_succ pulp rpm content list --name-in "${RPM_NAME}" --name-in "${RPM2_NAME}"
pulp rpm content list
expect_succ test "$(echo "${OUTPUT}" | jq -r 'length')" -eq 2

# test upload for advisory, package-upload is tested at the start
expect_succ pulp rpm content -t advisory upload --file "${TEST_ADVISORY}"
ADVISORY_HREF=$(echo "${OUTPUT}" | jq -r .pulp_href)
# make sure the package/advisory we've been playing with are cleaned up immediately
expect_succ pulp orphan cleanup --content-hrefs "[\"${PACKAGE_HREF}\",\"${ADVISORY_HREF}\"]" --protection-time 0 || true
