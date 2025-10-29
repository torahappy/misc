#!/bin/bash
set -eo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR"

git clone https://github.com/ggml-org/whisper.cpp
git clone https://github.com/flame/blis

pushd blis
./configure --prefix="$SCRIPT_DIR/bin" --enable-cblas -t openmp,pthreads auto
make -j
make install
popd

pushd whisper.cpp
export LD_LIBRARY_PATH="$SCRIPT_DIR/bin/lib:$SCRIPT_DIR/bin/lib64"
if ! command -v nvcc >/dev/null 2>&1
then
    cmake -B build -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=FLAME -DBLAS_INCLUDE_DIRS="$SCRIPT_DIR/bin/include/" -DCMAKE_INSTALL_PREFIX="$SCRIPT_DIR/bin/"
else
    cmake -B build -DGGML_CUDA=ON -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=FLAME -DBLAS_INCLUDE_DIRS="$SCRIPT_DIR/bin/include/" -DCMAKE_INSTALL_PREFIX="$SCRIPT_DIR/bin/"
fi
cmake --build build --config Release -j$(echo $(nproc) 2 / p | dc)
pushd build
make install
popd
./models/download-ggml-model.sh large-v3
popd

