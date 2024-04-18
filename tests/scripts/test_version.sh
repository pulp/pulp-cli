#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")"/config.source

expect_succ pulp --version
grep -q 'Pulp3 Command Line Interface, Version ' <<< "$OUTPUT"
grep -q 'common: ' <<< "$OUTPUT"
