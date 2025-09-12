#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

expect_succ pulp orphan cleanup

test "$(echo "${OUTPUT}" | jq -r '.state' )" = "completed"

pulp debug has-plugin --name "file" || exit 23

dd if=/dev/urandom of=test_1.txt bs=2MiB count=1

expect_succ pulp file content upload --file test_1.txt --relative-path orphan_test/test_1.txt
content_href=$(echo "${OUTPUT}" | jq -r .pulp_href)

expect_succ pulp orphan cleanup --content-hrefs "[\"$content_href\"]"
expect_succ pulp orphan cleanup --protection-time 10
