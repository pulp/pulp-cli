#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "certguard" --min-version "1.4.0" || exit 23

# Seems like the rhsm module is not installed on older oci_images
pulp debug has-plugin --name "core" --min-version "3.22" || exit 23

cleanup() {
  pulp content-guard rhsm destroy --name "cli_test_rhsm_guard" || true
}
trap cleanup EXIT

CACERTFILE="$(dirname "$(realpath "$0")")"/../../assets/artifacts/x509_ca.pem

expect_succ pulp content-guard rhsm create --name "cli_test_rhsm_guard" --ca-certificate "@$CACERTFILE"
expect_succ pulp content-guard rhsm list --name "cli_test_rhsm_guard"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp content-guard rhsm show --name "cli_test_rhsm_guard"
expect_succ pulp content-guard rhsm update --name "cli_test_rhsm_guard" --description "TO BE DELETED"
expect_succ pulp content-guard rhsm destroy --name "cli_test_rhsm_guard"
