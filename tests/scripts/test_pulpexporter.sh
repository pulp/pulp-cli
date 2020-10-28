#!/bin/sh

. "$(dirname "$(realpath $0)")/config.sh"
. "$(dirname "$(realpath $0)")/constants.sh"

RMOTE="cli_test_file_remote"
REPO1="cli_test_pulpexporter_repository_1"
REPO2="cli_test_pulpexporter_repository_2"
NAME1="cli_test_exporter_1"
NAME2="cli_test_exporter_2"
PATH1="/tmp/exports"
PATH2="/tmp/export-path-changed"

cleanup() {
  pulp_cli file remote destroy --name $RMOTE || true
  pulp_cli file repository destroy --name $REPO1 || true
  pulp_cli file repository destroy --name $REPO2 || true
  pulp_cli pulpexporter delete --name cli_test_exporter_1 || true
  pulp_cli pulpexporter delete --name cli_test_exporter_2 || true
}
trap cleanup EXIT

# Prepare
pulp_cli file remote create --name $RMOTE --url "$FILE_REMOTE_URL" | jq -r .name
pulp_cli file repository create --name $REPO1 | jq -r .name
pulp_cli file repository create --name $REPO2 | jq -r .name

# Test create
pulp_cli pulpexporter create --name $NAME1 --path $PATH1 --repository $REPO1 file --repository $REPO2 file
pulp_cli pulpexporter create --name $NAME2 --path $PATH1 --repository $REPO1 file --repository $REPO2 file

# Test list
pulp_cli pulpexporter list | jq -r '.results[].name'

# Test list-by-name
pulp_cli pulpexporter list --name $NAME1 | jq -r .count
pulp_cli pulpexporter list --name ${NAME1}_foo | jq -r .count

# Test update
pulp_cli pulpexporter update --name $NAME1 --path $PATH2 | jq -r '.'
pulp_cli pulpexporter list --name $NAME1 | jq -r .results[].path

# Test delete
! pulp_cli pulpexporter delete --name ${NAME1}_bar
pulp_cli pulpexporter delete --name $NAME1
pulp_cli pulpexporter delete --name $NAME2