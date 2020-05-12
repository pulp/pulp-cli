#!/bin/sh

. "$(dirname "$(realpath $0)")/config.sh"

pulp_cli file repository list
