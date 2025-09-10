#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" || exit 23

# This container seems to have issues with the compression format of the fixture.
pulp debug has-plugin --name "rpm" --specifier "==3.20.0" && pulp debug has-plugin --name "core" --specifier "==3.23.21" && exit 23

cleanup() {
  pulp rpm distribution destroy --name "cli_test_rpm_sync_distro" || true
  pulp rpm repository destroy --name "cli_test_rpm_sync_repository" || true
  pulp rpm remote destroy --name "cli_test_rpm_sync_remote" || true
  pulp rpm repository destroy --repository "cli_test_rpm_sync_repository2" || true
}
trap cleanup EXIT

# Add content using JSON file
cat <<EOT >> repo_config.json
{
"enabled":1,
"repo_gpgcheck":1,
"gpgcheck":1,
"skip_if_unavailable":false,
"assumeyes":true
}

EOT

expect_succ pulp rpm remote create --name "cli_test_rpm_sync_remote" --url "$RPM_REMOTE_URL"
expect_succ pulp rpm remote show --name "cli_test_rpm_sync_remote"
expect_succ pulp rpm repository create --name "cli_test_rpm_sync_repository" --remote "cli_test_rpm_sync_remote" --description "cli test repository"
expect_succ pulp rpm repository update --repository "cli_test_rpm_sync_repository" --description ""
expect_succ pulp rpm repository show --repository "cli_test_rpm_sync_repository"
test "$(echo "$OUTPUT" | jq -r '.description')" = "null"

# sqlite metadata removal from pulp_rpm (pulp/pulp_rpm#3328)
if pulp debug has-plugin --name "rpm" --specifier "<3.25.0"
then
  expect_succ pulp rpm repository update --name "cli_test_rpm_sync_repository" --no-sqlite-metadata
else
  expect_fail pulp rpm repository update --name "cli_test_rpm_sync_repository" --no-sqlite-metadata
fi

if pulp debug has-plugin --name "rpm" --specifier ">=3.24.0"
then
expect_succ pulp rpm repository create --name "cli_test_rpm_sync_repository2" --repo-config "@repo_config.json"
test "$(echo "$OUTPUT" | jq -r '.repo_config.assumeyes')" = "true"
fi

expect_succ pulp rpm repository sync --repository "cli_test_rpm_sync_repository" --skip-type srpm
if pulp debug has-plugin --name "rpm" --specifier ">=3.19.0"
then
  expect_succ pulp rpm repository sync --name "cli_test_rpm_sync_repository" --skip-type treeinfo
  expect_succ pulp rpm repository sync --name "cli_test_rpm_sync_repository" --skip-type treeinfo --skip-type srpm
fi
expect_succ pulp rpm repository sync --name "cli_test_rpm_sync_repository"

expect_succ pulp rpm publication create --repository "cli_test_rpm_sync_repository"
PUBLICATION_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)
expect_succ pulp rpm publication create --repository "cli_test_rpm_sync_repository" --version 0
PUBLICATION_VER_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)

if pulp debug has-plugin --name "rpm" --specifier ">=3.24.0"
then
expect_succ pulp rpm publication create --repository "cli_test_rpm_sync_repository" --repo-config "@repo_config.json"
test "$(echo "$OUTPUT" | jq -r '.repo_config.assumeyes')" = "true"
expect_succ pulp rpm publication destroy --href "$(echo "$OUTPUT" | jq -r '.pulp_href')"
fi

expect_succ pulp rpm distribution create --name "cli_test_rpm_sync_distro" \
  --base-path "cli_test_rpm_sync_distro" \
  --publication "$PUBLICATION_HREF"

if pulp debug has-plugin --name "rpm" --specifier ">=3.23.0"
then
  expect_succ pulp rpm distribution create --name "cli_test_rpm_sync_distro2" \
    --base-path "cli_test_rpm_sync_distro2" \
    --publication "$PUBLICATION_HREF" \
    --generate-repo-config
  expect_succ pulp rpm distribution destroy --name "cli_test_rpm_sync_distro2"
fi

expect_succ pulp rpm repository version list --repository "cli_test_rpm_sync_repository"
expect_succ pulp rpm repository version repair --repository "cli_test_rpm_sync_repository" --version 1

expect_succ pulp rpm repository update --name "cli_test_rpm_sync_repository" --retain-package-versions 2
expect_succ pulp rpm repository show --name "cli_test_rpm_sync_repository"
test "$(echo "$OUTPUT" | jq -r '.retain_package_versions')" = "2"

expect_succ pulp rpm repository sync --repository "cli_test_rpm_sync_repository" --optimize
expect_succ pulp rpm repository sync --repository "cli_test_rpm_sync_repository" --no-optimize

expect_succ pulp rpm repository update --repository "cli_test_rpm_sync_repository" --retain-package-versions 0
expect_succ pulp rpm repository sync --repository "cli_test_rpm_sync_repository" --sync-policy additive
expect_succ pulp rpm repository sync --repository "cli_test_rpm_sync_repository" --sync-policy mirror_complete
expect_succ pulp rpm repository sync --repository "cli_test_rpm_sync_repository" --sync-policy mirror_content_only
expect_fail pulp rpm repository sync --repository "cli_test_rpm_sync_repository" --sync-policy foobar

if pulp debug has-plugin --name "rpm" --specifier ">=3.25.0"
then
  expect_succ pulp rpm publication create --repository "cli_test_rpm_sync_repository" --checksum-type sha512
  expect_fail pulp rpm publication create --repository "cli_test_rpm_sync_repository" --checksum-type sha1

  expect_succ pulp rpm repository update --name "cli_test_rpm_sync_repository" --checksum-type sha512
  expect_fail pulp rpm repository update --name "cli_test_rpm_sync_repository" --checksum-type sha1
else
  expect_succ pulp rpm repository update --name "cli_test_rpm_sync_repository" --metadata-checksum-type sha1
  expect_succ pulp rpm repository update --name "cli_test_rpm_sync_repository" --package-checksum-type sha1
fi

expect_succ pulp rpm distribution destroy --name "cli_test_rpm_sync_distro"
expect_succ pulp rpm publication destroy --href "$PUBLICATION_HREF"
expect_succ pulp rpm publication destroy --href "$PUBLICATION_VER_HREF"
expect_succ pulp rpm repository destroy --repository "cli_test_rpm_sync_repository"
expect_succ pulp rpm remote destroy --remote "cli_test_rpm_sync_remote"

# auto-publish
expect_succ pulp rpm remote create --name "cli_test_rpm_sync_remote" --url "$RPM_REMOTE_URL"
expect_succ pulp rpm repository create --name "cli_test_rpm_sync_repository" --remote "cli_test_rpm_sync_remote" --autopublish

expect_succ pulp rpm distribution create --name "cli_test_rpm_sync_distro" \
  --base-path "cli_test_rpm_sync_distro" \
  --repository "cli_test_rpm_sync_repository"

expect_succ pulp rpm repository sync --repository "cli_test_rpm_sync_repository"
if pulp debug has-plugin --name "rpm" --specifier ">=3.20.0"
then
  expect_succ pulp rpm publication list --repository rpm:rpm:cli_test_rpm_sync_repository
else
  expect_succ pulp rpm publication list
fi
test "$(echo "$OUTPUT" | jq -r length)" -ge "1"
