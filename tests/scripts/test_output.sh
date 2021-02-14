#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")"/config.source

# skip this test if pygments is not installed
pip show pygments > /dev/null || exit 3

# the foreground color escape sequence is "ESC[38;5"
output=$(script -qefc "pulp status")
if [[ "$output" != *"[38;5"* ]]
then
  echo "Did not detect color output in 'pulp status'"
  exit 1
fi

output=$(pulp status | cat)
if [[ "$output" == *"[38;5"* ]]
then
  echo "Detected color output in piped 'pulp status'"
  exit 1
fi
