#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

# Test that help pages are shown without an error
expect_succ pulp --base-url "http://invalid" status --help
expect_succ pulp --base-url "http://invalid" artifact
expect_succ pulp --base-url "http://invalid" artifact --help
expect_succ pulp --base-url "http://invalid" artifact list --help
expect_succ pulp --base-url "http://invalid" artifact show --help

expect_succ pulp --base-url "http://invalid" file
expect_succ pulp --base-url "http://invalid" file --help
expect_succ pulp --base-url "http://invalid" file remote
expect_succ pulp --base-url "http://invalid" file remote --help
expect_succ pulp --base-url "http://invalid" file remote create --help
expect_succ pulp --base-url "http://invalid" file repository create --help
expect_succ pulp --base-url "http://invalid" file repository update --help
expect_succ pulp --base-url "http://invalid" file repository sync --help
expect_succ pulp --base-url "http://invalid" file repository version
expect_succ pulp --base-url "http://invalid" file repository version --help
expect_succ pulp --base-url "http://invalid" file repository version list --help
expect_succ pulp --base-url "http://invalid" file repository version show --help
expect_succ pulp --base-url "http://invalid" file repository version repair --help
expect_succ pulp --base-url "http://invalid" file repository version destroy --help

# Test that this command complains about the missing repository
expect_fail pulp --base-url "http://invalid" file repository version list
echo "$ERROUTPUT" | expect_succ grep -q "A repository must be specified"
