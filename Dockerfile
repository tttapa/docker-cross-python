ARG HOST_TRIPLE

# Build native Python

FROM ubuntu:jammy AS native-build

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y \
        libbz2-dev libffi-dev libgdbm-dev libgdbm-compat-dev liblzma-dev \
        libncurses5-dev libreadline6-dev libsqlite3-dev libssl-dev \
        lzma lzma-dev uuid-dev zlib1g-dev \
        wget ca-certificates \
        build-essential && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ARG PYTHON_VERSION
ARG PYTHON_VERSION_SUFFIX=""
ENV PYTHON_VERSION ${PYTHON_VERSION}
ENV PYTHON_VERSION_SUFFIX ${PYTHON_VERSION_SUFFIX}
ENV PYTHON_VERSION_FULL ${PYTHON_VERSION}${PYTHON_VERSION_SUFFIX}

COPY build-native.sh .
RUN wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION_FULL}.tgz"
RUN bash build-native.sh

# Build cross Python

FROM ghcr.io/tttapa/toolchains:${HOST_TRIPLE} AS cross-build

ARG HOST_TRIPLE
ENV HOST_TRIPLE ${HOST_TRIPLE}

ARG PYTHON_VERSION
ARG PYTHON_VERSION_SUFFIX=""
ENV PYTHON_VERSION ${PYTHON_VERSION}
ENV PYTHON_VERSION_SUFFIX ${PYTHON_VERSION_SUFFIX}
ENV PYTHON_VERSION_FULL ${PYTHON_VERSION}${PYTHON_VERSION_SUFFIX}

USER root

COPY --from=native-build /opt/python-${PYTHON_VERSION_FULL} /
RUN test "$(python3 --version)" = "Python ${PYTHON_VERSION_FULL}"

COPY --from=native-build "/Python-${PYTHON_VERSION_FULL}.tgz" /

ENV TOOLCHAIN_PATH="/home/develop/opt/${HOST_TRIPLE}"
ENV PATH "$TOOLCHAIN_PATH/bin:$PATH"

COPY build-cross.sh .
RUN bash build-cross.sh

# Copy to clean image

FROM ubuntu:jammy

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        git wget ca-certificates \
        cmake ninja-build make pkg-config \
        libgdbm-compat4 libgdbm6 libreadline8 readline-common \
        libsqlite3-0 lzma \
        xz-utils bzip2 zstd && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ARG HOST_TRIPLE
ENV HOST_TRIPLE ${HOST_TRIPLE}

ARG PYTHON_VERSION
ARG PYTHON_VERSION_SUFFIX=""
ENV PYTHON_VERSION ${PYTHON_VERSION}
ENV PYTHON_VERSION_SUFFIX ${PYTHON_VERSION_SUFFIX}
ENV PYTHON_VERSION_FULL ${PYTHON_VERSION}${PYTHON_VERSION_SUFFIX}

COPY --from=native-build /opt/python-${PYTHON_VERSION_FULL} /
COPY --from=cross-build /home/develop/opt /opt/x-tools/
COPY --from=cross-build /opt/${HOST_TRIPLE} /opt/${HOST_TRIPLE}
RUN ln -s python3-config /usr/local/bin/python-config && \
    ln -s python3 /usr/local/bin/python && \
    ln -s pip3 /usr/local/bin/pip
ENV PATH "/opt/x-tools/${HOST_TRIPLE}/bin:$PATH"

RUN python3 -m ensurepip && \
    python3 -m pip install -U pip conan build

COPY *.py /opt/${HOST_TRIPLE}/scripts/
RUN mkdir -p /opt/${HOST_TRIPLE}/cmake && \
    python /opt/${HOST_TRIPLE}/scripts/gen-cmake-toolchain.py \
        ${HOST_TRIPLE} /opt/${HOST_TRIPLE}/cmake/${HOST_TRIPLE}.toolchain.cmake
RUN mkdir -p /opt/${HOST_TRIPLE}/cmake && \
    python /opt/${HOST_TRIPLE}/scripts/gen-py-build-cmake-cross-config.py \
        ${HOST_TRIPLE} /opt/${HOST_TRIPLE}/cmake/${HOST_TRIPLE}.py-build-cmake.cross.toml
RUN mkdir -p /opt/${HOST_TRIPLE}/conan/profiles && \
    python /opt/${HOST_TRIPLE}/scripts/gen-conan-profile.py \
        ${HOST_TRIPLE} /opt/${HOST_TRIPLE}/conan/profiles/${HOST_TRIPLE}
RUN chmod -R a-w /opt
