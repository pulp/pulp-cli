#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")"/config.source

# skip this test if pygments is not installed
pip show pygments > /dev/null || exit 3

# the foreground color escape sequence is "ESC[38;5"
expect_succ script -qefc "pulp status"
if [[ "$OUTPUT" != *"[38;5"* ]]
then
  echo "FAILURE: Did not detect color output in 'pulp status'" >&2
  exit 1
fi

expect_succ pulp status
if [[ "$OUTPUT" == *"[38;5"* ]]
then
  echo "FAILURE: Detected color output in piped 'pulp status'" >&2
  exit 1
fi
