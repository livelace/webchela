#!/usr/bin/env bash

set -x

exec >/tmp/debug 2>&1

TOTAL_ARGS="$#"

ORIGINAL_ARGS=("${@:3:TOTAL_ARGS}")
PORT_ARG=$1
ORIGINAL_BINARY=$2

exec vglrun "$ORIGINAL_BINARY" "$PORT_ARG" "${ORIGINAL_ARGS[@]}"
