#!/bin/sh
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

RMOTE="cli_test_file_remote"
REPO1="cli_test_pulpexporter_repository_1"
REPO2="cli_test_pulpexporter_repository_2"
NAME1="cli_test_exporter_1"
NAME2="cli_test_exporter_2"
PATH1="/tmp/exports"
PATH2="/tmp/export-path-changed"

cleanup() {
  pulp file remote destroy --name $RMOTE || true
  pulp file repository destroy --name $REPO1 || true
  pulp file repository destroy --name $REPO2 || true
  pulp exporter pulp destroy --name $NAME1 || true
  pulp exporter pulp destroy --name $NAME2 || true
}
trap cleanup EXIT

# Prepare
expect_succ pulp file remote create --name $RMOTE --url "$FILE_REMOTE_URL"
expect_succ pulp file repository create --name $REPO1
expect_succ pulp file repository sync --name $REPO1 --remote $RMOTE
expect_succ pulp file repository create --name $REPO2

# Test create
expect_succ pulp exporter pulp create --name $NAME1 --path $PATH1 --repository $REPO1 file --repository $REPO2 file
expect_succ pulp exporter pulp create --name $NAME2 --path $PATH1 --repository $REPO1 file

# Test read
expect_succ pulp exporter pulp show --name $NAME1

# Test list
expect_succ pulp exporter pulp list

# Test list-by-name
expect_succ pulp exporter pulp list --name $NAME1
expect_succ pulp exporter pulp list --name ${NAME1}_foo

# Test update
pulp exporter pulp update --name $NAME1 --path $PATH2
pulp exporter pulp list --name $NAME1

# Test export
expect_succ pulp export pulp run --exporter $NAME1
expect_succ pulp export pulp run --exporter $NAME1 --full False
expect_succ pulp export pulp run --exporter $NAME1 --full True --chunk-size 5KB
expect_succ pulp export pulp run --exporter $NAME2 --full False --start-versions $REPO1 file 0
expect_succ pulp export pulp run --exporter $NAME2 --full False --versions $REPO1 file 0
expect_succ pulp export pulp run --exporter $NAME2 --full False --start-versions $REPO1 file 0 --versions $REPO1 file 1
expect_succ pulp export pulp run --exporter $NAME2 --full False --start-versions $REPO1 file 0 --versions $REPO1 file 1 --chunk-size 5KB

# Test list exports
expect_succ pulp export pulp list --exporter $NAME1

# Test delete export
HREF=$(pulp export pulp list --exporter $NAME1 |  jq -r '.[0].pulp_href')
expect_succ pulp export pulp destroy --href "$HREF"

# Test delete exporter
expect_fail pulp  exporter pulp destroy --name ${NAME1}_bar
