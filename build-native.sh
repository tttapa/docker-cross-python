#!/usr/bin/env bash

# Script to download and build Python 3 from source

set -ex

version="${PYTHON_VERSION}"
builddir="/tmp/build-native"
python="Python-$version"
prefix="/usr/local"

mkdir -p "$builddir" && pushd $_
tar xzf /home/develop/$python.tgz
pushd "$python"

./configure --prefix="$prefix" \
    --enable-ipv6 \
    --enable-shared \
    'LDFLAGS=-Wl,-rpath,\$$ORIGIN/../lib'
    # --with-lto --enable-optimizations # TODO!

make -j$(($(nproc) + 2))
make install DESTDIR="$HOME/staging-python"

popd
popd
rm -rf "$builddir"