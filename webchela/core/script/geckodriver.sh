#!/usr/bin/env bash

set -x

# The main purpose of this script is providing
# a dedicated temporary directory to original geckodriver process.
# It needs for browser profile directory creation in a provided directory.
# BTW, chrome browser can easily create profile with "user-data-dir" in any place (even in marionette mode).

ALL_ARGS=("$@")
TOTAL_ARGS="$#"

ORIGINAL_OFFSET=$((TOTAL_ARGS-2))
ORIGINAL_ARGS=("${@:1:ORIGINAL_OFFSET}")

ORIGINAL_BINARY=${ALL_ARGS[ORIGINAL_OFFSET]}
TEMP_DIR=${ALL_ARGS[ORIGINAL_OFFSET+1]}


if [[ ! "$ORIGINAL_BINARY" || ! "$TEMP_DIR" ]];then
  echo "ERROR: Usage $0 <ORIGINAL_ARGS> /path/to/original/geckodriver /path/to/custom/temp/dir"
  exit 1
fi

if [ ! -f "$ORIGINAL_BINARY" ];then
  echo "ERROR: Binary file not found: $ORIGINAL_BINARY"
  exit 1
fi

if [ ! -d "$TEMP_DIR" ];then
  echo "ERROR: Temporary dir not found: $TEMP_DIR"
  exit 1
fi

export TMPDIR="$TEMP_DIR"
export TEMP="$TEMP_DIR"
export TMP="$TEMP_DIR"

# exec is needed for correct quitting of geckodriver.
exec "$ORIGINAL_BINARY" $(echo ${ORIGINAL_ARGS[*]})