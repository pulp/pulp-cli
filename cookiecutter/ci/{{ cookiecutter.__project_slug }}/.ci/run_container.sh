#!/bin/sh

# This file is shared between some projects please keep all copies in sync
# Known places:
#   - https://github.com/pulp/pulp-cli/blob/main/.ci/run_container.sh
#   - https://github.com/pulp/pulp-cli-deb/blob/main/.ci/run_container.sh
#   - https://github.com/pulp/pulp-cli-gem/blob/main/.ci/run_container.sh
#   - https://github.com/pulp/pulp-cli-maven/blob/main/.ci/run_container.sh
#   - https://github.com/pulp/pulp-cli-ostree/blob/main/.ci/run_container.sh
#   - https://github.com/pulp/squeezer/blob/develop/tests/run_container.sh

set -eu

BASEPATH="$(dirname "$(readlink -f "$0")")"
export BASEPATH

if [ -z "${CONTAINER_RUNTIME:+x}" ]
then
  if ls /usr/bin/podman
  then
    CONTAINER_RUNTIME=podman
  else
    CONTAINER_RUNTIME=docker
  fi
fi
export CONTAINER_RUNTIME

if [ -z "${KEEP_CONTAINER:+x}" ]
then
  RM="yes"
else
  RM=""
fi

IMAGE_TAG="${IMAGE_TAG:-latest}"
FROM_TAG="${FROM_TAG:-latest}"

if [ "${CONTAINER_FILE:+x}" ]
then
  IMAGE_TAG="ephemeral-build"
  "${CONTAINER_RUNTIME}" build --file "${BASEPATH}/assets/${CONTAINER_FILE}" --build-arg FROM_TAG="${FROM_TAG}" --tag ghcr.io/pulp/pulp:"${IMAGE_TAG}" .
fi

if [ "$(getenforce)" = "Enforcing" ]; then
    SELINUX="yes"
else
    SELINUX=""
fi;

"${CONTAINER_RUNTIME}" run ${RM:+--rm} --env S6_KEEP_ENV=1 ${PULP_API_ROOT:+--env PULP_API_ROOT} --detach --name "pulp-ephemeral" --volume "${BASEPATH}/settings:/etc/pulp${SELINUX:+:Z}" --publish "8080:80" "ghcr.io/pulp/pulp:${IMAGE_TAG}"

# shellcheck disable=SC2064
trap "${CONTAINER_RUNTIME} stop pulp-ephemeral" EXIT
# shellcheck disable=SC2064
trap "${CONTAINER_RUNTIME} stop pulp-ephemeral" INT

echo "Wait for pulp to start."
for counter in $(seq 40 -1 0)
do
  if [ "$counter" = "0" ]
  then
    echo "FAIL."
    "${CONTAINER_RUNTIME}" images
    "${CONTAINER_RUNTIME}" ps -a
    "${CONTAINER_RUNTIME}" logs "pulp-ephemeral"
    exit 1
  fi

  sleep 3
  if curl --fail "http://localhost:8080${PULP_API_ROOT:-/pulp/}api/v3/status/" > /dev/null 2>&1
  then
    echo "SUCCESS."
    break
  fi
  echo "."
done

# show pulpcore/plugin versions we're using
curl -s "http://localhost:8080${PULP_API_ROOT:-/pulp/}api/v3/status/" | jq '.versions|map({key: .component, value: .version})|from_entries'

# Set admin password
"${CONTAINER_RUNTIME}" exec "pulp-ephemeral" pulpcore-manager reset-admin-password --password password

if [ -d "${BASEPATH}/container_setup.d/" ]
then
  run-parts --regex '^[0-9]+-[-_[:alnum:]]*\.sh$' "${BASEPATH}/container_setup.d/"
fi

PULP_LOGGING="${CONTAINER_RUNTIME}" "$@"
