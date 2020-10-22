#!/bin/sh

. "$(dirname "$(realpath $0)")/config.sh"

STATUS_RESULT=$(pulp_cli -v status 2>&1 >/dev/null)

echo ${STATUS_RESULT} | grep -q "^get https\?://\w.*/pulp/api/v3/status/$"
