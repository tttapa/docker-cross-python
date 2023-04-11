#!/usr/bin/env bash

# Script to cross-compile Python 3 from source
# (minimal install for linking, not for direct deployment)

set -ex

# Paths
version="${PYTHON_VERSION}"
builddir="/tmp/build-cross"
python="Python-$version"
prefix="/usr/local"
staging="/opt/${HOST_TRIPLE}/python-$version"

# Extract
mkdir -p "$builddir" && pushd $_
tar xzf /$python.tgz
pushd "$python"

# Patch setup.py
if [ -e setup.py ]; then
    sed -i 's@# Debian/Ubuntu multiarch support.@return@g' setup.py
fi

# Configure
echo -e "ac_cv_file__dev_ptmx=yes\nac_cv_file__dev_ptc=no" > config.site
CONFIG_SITE="$PWD/config.site" \
./configure \
    --enable-ipv6 \
    --enable-shared \
    --disable-test-modules \
    --build="x86_64-linux-gnu" \
    --host="${HOST_TRIPLE}" \
    --prefix="$prefix" \
    --with-build-python="$(which python3)"

# Patch makefile to install static libraries
sed -i 's@libainstall:\( \|	\)all@libainstall:@g' Makefile

# Build & install
mkdir -p "$staging"
make python python-config -j$(($(nproc) + 2))
make altbininstall inclinstall libainstall bininstall DESTDIR="$staging"
ln -s python-$version "$staging/../python${version%.*}"

# Clean up
popd
popd
rm -rf "$builddir"
