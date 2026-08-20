#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

eval "$(pulp status | jq -r '.domain_enabled // false')" || exit 23

DOMAIN="cli_test_orphans"

cleanup() {
  pulp domain destroy --name "$DOMAIN" || true
}
trap cleanup EXIT

# Setup test domain to avoid other tests
expect_succ pulp domain create --name "$DOMAIN" --storage-class "pulpcore.app.models.storage.FileSystem" --storage-settings '{"location": "/var/lib/pulp/media"}'

expect_succ pulp --domain "$DOMAIN" orphan cleanup

test "$(echo "${OUTPUT}" | jq -r '.state' )" = "completed"

pulp debug has-plugin --name "file" || exit 23

dd if=/dev/urandom of=test_1.txt bs=2MiB count=1

expect_succ pulp --domain "$DOMAIN" file content upload --file test_1.txt --relative-path orphan_test/test_1.txt
content_href=$(echo "${OUTPUT}" | jq -r .pulp_href)

expect_succ pulp --domain "$DOMAIN" orphan cleanup --content-hrefs "[\"$content_href\"]"
expect_succ pulp --domain "$DOMAIN" orphan cleanup --protection-time 10
