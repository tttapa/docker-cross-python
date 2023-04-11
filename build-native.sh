#!/usr/bin/env bash

# Script to build Python 3 from source

set -ex

# Paths
version="${PYTHON_VERSION_FULL}"
builddir="/tmp/build-native"
python="Python-$version"
prefix="/usr/local"
staging="/opt/python-$version"

# Extract
mkdir -p "$builddir" && pushd $_
tar xzf /$python.tgz
pushd "$python"

# Configure
./configure --prefix="$prefix" \
    --enable-ipv6 \
    --enable-shared \
    'LDFLAGS=-Wl,-rpath,\$$ORIGIN/../lib'
    # --with-lto --enable-optimizations # TODO!

# Build & install
mkdir -p "$staging"
make -j$(($(nproc) + 2))
make install DESTDIR="$staging"

# Clean up
popd
popd
rm -rf "$builddir"
