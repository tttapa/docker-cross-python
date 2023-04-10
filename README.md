# docker-cross-python

Cross-compiles a basic version of Python (without most dependencies and without
PGO or LTO) to link against when cross-compiling Python extension modules.

Download the compiled binaries from the [Releases page](https://github.com/tttapa/docker-cross-python/releases).

## Docker container

Docker containers are available from the [Packages page](https://github.com/tttapa/docker-cross-python/pkgs/container/docker-cross-python).
They are Ubuntu containers with the following additions:
 - GCC 12.2 cross-compilation toolchain (`/opt/x-tools/<host-triple>`)
 - Native Python installation (`/usr/local/python`)
 - Cross-compiled Python installation (`/opt/<host-triple>/python-<version>`)
