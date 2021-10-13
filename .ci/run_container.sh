#!/bin/sh

set -eu

BASEPATH="$(dirname "$(readlink -f "$0")")"

if [ -z "${CONTAINER_RUNTIME:+x}" ]
then
  if ls /usr/bin/podman
  then
    CONTAINER_RUNTIME=podman
  else
    CONTAINER_RUNTIME=docker
  fi
fi

if [ -z "${KEEP_CONTAINER:+x}" ]
then
  RM="yes"
else
  RM=""
fi

"${CONTAINER_RUNTIME}" run ${RM:+--rm} --detach --name "pulp-ephemeral" --volume "${BASEPATH}/settings:/etc/pulp" --publish "8080:80" "pulp/pulp:${IMAGE_TAG:-latest}"

# shellcheck disable=SC2064
trap "${CONTAINER_RUNTIME} stop pulp-ephemeral" EXIT
# shellcheck disable=SC2064
trap "${CONTAINER_RUNTIME} stop pulp-ephemeral" INT

echo "Wait for pulp to start."
for counter in $(seq 20)
do
  sleep 3
  if curl --fail http://localhost:8080/pulp/api/v3/status/ > /dev/null 2>&1
  then
    echo "SUCCESS."
    break
  fi
  echo "."
done
if [ "$counter" = "0" ]
then
  echo "FAIL."
  "${CONTAINER_RUNTIME}" images
  "${CONTAINER_RUNTIME}" ps -a
  "${CONTAINER_RUNTIME}" logs "pulp-ephemeral"
  exit 1
fi

# show pulpcore/plugin versions we're using
curl -s http://localhost:8080/pulp/api/v3/status/ | jq '.versions|map({key: .component, value: .version})|from_entries'

# Set admin password
"${CONTAINER_RUNTIME}" exec "pulp-ephemeral" pulpcore-manager reset-admin-password --password password

if pulp --base-url "http://localhost:8080" --username "admin" --password "password" debug has-plugin --name "core" --min-version 3.11
then
  # Setup a signing service
  "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /root/sign_deb_release.sh" < "${BASEPATH}/../tests/assets/sign_deb_release.sh"
  "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /tmp/setup_signing_service.py" < "${BASEPATH}/../tests/assets/setup_signing_service.py"
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-KEY-pulp-qe | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /tmp/GPG-KEY-pulp-qe"
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-PRIVATE-KEY-pulp-qe | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" gpg --import
  echo "6EDF301256480B9B801EBA3D05A5E6DA269D9D98:6:" | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" gpg --import-ownertrust
  "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" chmod a+x /root/sign_deb_release.sh /tmp/setup_signing_service.py
  "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" /tmp/setup_signing_service.py /root/sign_deb_release.sh /tmp/GPG-KEY-pulp-qe
fi

PULP_LOGGING="${CONTAINER_RUNTIME}" "$@"
