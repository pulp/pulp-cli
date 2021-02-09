#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

good_settings="${XDG_CONFIG_HOME}/pulp/settings.toml"
bad_settings="bad_settings.toml"
test_settings="test.toml"

export XDG_CONFIG_HOME=/nowhere

# SETTINGS OPTION

sed -e '/base_url/c\base_url = "http://badurl"' "$good_settings" > "$bad_settings"

expect_succ pulp --config "$good_settings" file repository list
expect_succ pulp --config "$bad_settings" --base-url "$PULP_BASE_URL" file repository list

expect_fail pulp --config "$bad_settings" file repository list
expect_fail pulp --config "$good_settings" --base-url "http://badurl" file repository list

# fail as both username and password are required together
expect_fail pulp --password test file repository list

# fail when using basic auth and cert auth
expect_fail pulp --username test --password test --client "/some/path" status

# fail when using basic auth and cert auth
expect_fail pulp --key "/some/path" file remote list


# CONFIG COMMAND

expect_fail pulp config edit --location $test_settings

expect_succ pulp config create --location $test_settings --base-url "http://testing"
grep 'base_url = "http://testing"' $test_settings
grep 'verify_ssl = true' $test_settings

expect_fail pulp config create --location $test_settings
expect_succ pulp config create --location $test_settings --overwrite

expect_succ pulp config validate --strict --location $test_settings
