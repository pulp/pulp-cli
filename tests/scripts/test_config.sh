#!/bin/sh

. "$(dirname "$(realpath "$0")")/config.source"

good_settings="good_settings.toml"
bad_settings="bad_settings.toml"
good_cli="$PULP_CLI --config $good_settings"
bad_cli="$PULP_CLI --config $bad_settings"

cleanup() {
  rm $good_settings || true
  rm $bad_settings || true
}
trap cleanup EXIT

cat >$good_settings <<EOL
[cli]
base_url = "$PULP_BASE_URL"
user = "$PULP_USER"
password = "$PULP_PASSWORD"
EOL

cat >$bad_settings <<EOL
[cli]
base_url = "http://badurl"
user = "$PULP_USER"
password = "$PULP_PASSWORD"
EOL

$good_cli file repository list
$bad_cli --base-url "$PULP_BASE_URL" file repository list

if $bad_cli file repository list 2> /dev/null; then
  echo "'$bad_cli ...' succeeded unexpectedly"
  exit 1
fi

if $good_cli --base-url "http://badurl" file repository list 2> /dev/null; then
  echo "'$good_cli --base-url http://badurl ...' succeeded unexpectedly"
  exit 1
fi

# fail as both username and password are required together
if $PULP_CLI --password test file repository list 2> /dev/null; then
  echo "'$PULP_CLI --password test ...' succeeded unexpectedly"
  exit 1
fi
