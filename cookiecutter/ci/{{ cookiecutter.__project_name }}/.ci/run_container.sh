#!/bin/sh

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

TMPDIR="$(mktemp -d)"

cleanup () {
  "${CONTAINER_RUNTIME}" stop pulp-ephemeral && true
  rm -rf "${TMPDIR}"
}

trap cleanup EXIT
trap cleanup INT

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

mkdir -p "${TMPDIR}/settings/certs"
cp "${BASEPATH}/settings/settings.py" "${TMPDIR}/settings"

if [ -z "${PULP_HTTPS:+x}" ]
then
  PROTOCOL="http"
  PORT="80"
  PULP_CONTENT_ORIGIN="http://localhost:8080/"
else
  PROTOCOL="https"
  PORT="443"
  PULP_CONTENT_ORIGIN="https://localhost:8080/"
  python3 -m trustme -d "${TMPDIR}/settings/certs"
  export PULP_CA_BUNDLE="${TMPDIR}/settings/certs/client.pem"
  ln -fs server.pem "${TMPDIR}/settings/certs/pulp_webserver.crt"
  ln -fs server.key "${TMPDIR}/settings/certs/pulp_webserver.key"
fi
export PULP_CONTENT_ORIGIN

"${CONTAINER_RUNTIME}" \
  run ${RM:+--rm} \
  --env S6_KEEP_ENV=1 \
  ${PULP_HTTPS:+--env PULP_HTTPS} \
  ${PULP_API_ROOT:+--env PULP_API_ROOT} \
  --env PULP_CONTENT_ORIGIN \
  --detach \
  --name "pulp-ephemeral" \
  --volume "${TMPDIR}/settings:/etc/pulp${SELINUX:+:Z}" \
  --publish "8080:${PORT}" \
  "ghcr.io/pulp/pulp:${IMAGE_TAG}"

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
  if curl --insecure --fail "${PROTOCOL}://localhost:8080${PULP_API_ROOT:-/pulp/}api/v3/status/" > /dev/null 2>&1
  then
    echo "SUCCESS."
    break
  fi
  echo "."
done

# Set admin password
"${CONTAINER_RUNTIME}" exec "pulp-ephemeral" pulpcore-manager reset-admin-password --password password

# Create pulp config
PULP_CLI_CONFIG="${TMPDIR}/settings/certs/cli.toml"
export PULP_CLI_CONFIG
pulp config create --overwrite --location "${PULP_CLI_CONFIG}" --base-url "${PROTOCOL}://localhost:8080" ${PULP_API_ROOT:+--api-root "${PULP_API_ROOT}"} --username "admin" --password "password"
# show pulpcore/plugin versions we're using
pulp --config "${PULP_CLI_CONFIG}" --refresh-api status

if [ -d "${BASEPATH}/container_setup.d/" ]
then
  run-parts --exit-on-error --regex '^[0-9]+-[-_[:alnum:]]*\.sh$' "${BASEPATH}/container_setup.d/"
fi

PULP_LOGGING="${CONTAINER_RUNTIME}" "$@"
