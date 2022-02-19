#!/usr/bin/env bash

# Script to download and build Python 3 from source

set -ex

version="${PYTHON_VERSION}"
builddir="/tmp/build-cross"
python="Python-$version"
prefix="/usr/local"

mkdir -p "$builddir" && pushd $_
tar xzf /home/develop/$python.tgz
pushd "$python"

# Configure
echo -e "ac_cv_file__dev_ptmx=yes\nac_cv_file__dev_ptc=no" > config.site
CONFIG_SITE="$PWD/config.site" \
./configure \
    --enable-ipv6 \
    --enable-shared \
    --with-ensurepip=install \
    --build="$(gcc -dumpmachine)" \
    --host="${HOST_TRIPLE}" \
    --prefix="/usr/local" \
    CFLAGS="--sysroot=${HOST_SYSROOT} \
                -I${HOST_SYSROOT}/usr/local/include \
                -L${HOST_SYSROOT}/usr/local/lib" \
    CPPFLAGS="--sysroot=${HOST_SYSROOT} \
                -I${HOST_SYSROOT}/usr/local/include" \
    CXXFLAGS="--sysroot=${HOST_SYSROOT} \
                -I${HOST_SYSROOT}/usr/local/include \
                -L${HOST_SYSROOT}/usr/local/lib" \
    LDFLAGS="--sysroot=${HOST_SYSROOT} \
                -L${HOST_SYSROOT}/usr/local/lib"
    # --with-lto --enable-optimizations 
    # --enable-loadable-sqlite-extensions --with-dbmliborder=bdb:gdbm
cat config.log

# Build
make -j$(($(nproc) + 2))

# Install
make install DESTDIR="${HOST_SYSROOT}"
# make install DESTDIR="${HOST_STAGING}"

# Cleanup
popd
popd
rm -rf "$builddir"
