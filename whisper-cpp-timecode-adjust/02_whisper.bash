#!/bin/bash
set -eo pipefail

if [ -z ${TARGET_LANG+x} ]; then TARGET_LANG=en; fi
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR"

export LD_LIBRARY_PATH="$SCRIPT_DIR/bin/lib:$SCRIPT_DIR/bin/lib64"

find ./orig/ -name "*.wav" | xargs ./bin/bin/whisper-cli -m ./whisper.cpp/models/ggml-large-v3.bin -t $(echo $(nproc) 2 / p | dc) -l $TARGET_LANG -oj

