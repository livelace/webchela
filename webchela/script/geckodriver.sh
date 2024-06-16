#!/usr/bin/env bash

set -x

# The main purpose of this script is providing
# a dedicated temporary directory to original geckodriver process.
# It needs for browser profile directory creation in a provided directory.
# BTW, chrome browser can easily create profile with "user-data-dir" in any place (even in marionette mode).

TOTAL_ARGS="$#"

ORIGINAL_ARGS=("${@:7:TOTAL_ARGS}")
LOG_ARG=$1
LOG_LEVEL=$2
ORIGINAL_BINARY=$5
TEMP_DIR=$6

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
# shellcheck disable=SC2068
exec vglrun "$ORIGINAL_BINARY" "$LOG_ARG" "$LOG_LEVEL" ${ORIGINAL_ARGS[@]}
