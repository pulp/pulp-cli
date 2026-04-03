#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rust" || exit 23

expect_succ pulp rust content list
expect_succ pulp rust content list --limit 5
expect_succ pulp rust content list --name "itoa"
expect_succ pulp rust content list --version "1.0.0"
