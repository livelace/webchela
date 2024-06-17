#!/usr/bin/env bash

set -x

TOTAL_ARGS="$#"

ORIGINAL_ARGS=("${@:3:TOTAL_ARGS}")
PORT_ARG=$1
ORIGINAL_BINARY=$2

# virtualgl gpu offloading, can work without Xorg server available:
exec vglrun "$ORIGINAL_BINARY" "$PORT_ARG" "${ORIGINAL_ARGS[@]}"
