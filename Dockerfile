ARG HOST_TRIPLE

# Build native Python

FROM ghcr.io/tttapa/docker-crosstool-ng-multiarch:master AS py-build

USER root
RUN apt-get update && \
    apt-get install -y \
        zlib1g-dev libbz2-dev libssl-dev uuid-dev libffi-dev libreadline-dev \
        libsqlite3-dev libbz2-dev libncurses5-dev libreadline6-dev \
        libgdbm-dev libgdbm-compat-dev liblzma-dev && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
USER develop

ARG PYTHON_VERSION
ARG PYTHON_VERSION ${PYTHON_VERSION}

WORKDIR /home/develop
RUN wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
COPY --chown=develop:develop build-native.sh .
RUN bash build-native.sh

# Build cross Python

FROM ghcr.io/tttapa/docker-arm-cross-toolchain:${HOST_TRIPLE}

ARG HOST_TRIPLE
ENV HOST_TRIPLE ${HOST_TRIPLE}

ARG PYTHON_VERSION
ARG PYTHON_VERSION ${PYTHON_VERSION}

WORKDIR /home/develop
COPY --from=py-build --chown=root /home/develop/staging-python /
RUN test "$(python3 --version)" = "Python ${PYTHON_VERSION}"

COPY --from=py-build "/home/develop/Python-${PYTHON_VERSION}.tgz" /home/develop

ENV TOOLCHAIN_PATH="/home/develop/x-tools/${HOST_TRIPLE}"
ENV HOST_SYSROOT="/home/develop/sysroot"
# ENV HOST_STAGING="/home/develop/staging"

# RUN . ~/host-config/.env && \
#     mkdir -p ${HOST_STAGING}/usr/local && \
#     [ "${HOST_BITNESS}" -eq "64" ] && \
#     ln -s lib "${HOST_STAGING}/usr/local/lib64" || \
#     true
RUN mkdir "${HOST_SYSROOT}" && \
    cp -a "${TOOLCHAIN_PATH}/${HOST_TRIPLE}/sysroot/"* "${HOST_SYSROOT}"/ && \
    chmod -R u+w "${HOST_SYSROOT}"
RUN . ~/host-config/.env && \
    mkdir -p ${HOST_SYSROOT}/usr/local && \
    [ "${HOST_BITNESS}" -eq "64" ] && \
    ln -s lib "${HOST_SYSROOT}/usr/local/lib64" || \
    true

COPY --chown=develop:develop build-cross.sh .
RUN bash build-cross.sh
