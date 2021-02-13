#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "pulp_2to3_migration" || exit 3

expect_succ pulp migration pulp2 repository list
expect_succ pulp migration pulp2 content list
