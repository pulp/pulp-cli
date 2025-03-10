#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "certguard" --specifier ">=1.4.0" || exit 23

cleanup() {
  pulp content-guard x509 destroy --name "cli_test_x509_guard" || true
}
trap cleanup EXIT

CACERTFILE="$(dirname "$(realpath "$0")")"/../../assets/artifacts/x509_ca.pem

expect_succ pulp content-guard x509 create --name "cli_test_x509_guard" --ca-certificate "@$CACERTFILE"
expect_succ pulp content-guard x509 list --name "cli_test_x509_guard"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp content-guard x509 show --name "cli_test_x509_guard"
expect_succ pulp content-guard x509 update --name "cli_test_x509_guard" --description "TO BE DELETED"
expect_succ pulp content-guard x509 destroy --name "cli_test_x509_guard"
