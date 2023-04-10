ARG HOST_TRIPLE

# Build native Python

FROM ubuntu:jammy AS native-build

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y \
        zlib1g-dev libbz2-dev libssl-dev uuid-dev libffi-dev libreadline-dev \
        libsqlite3-dev libbz2-dev libncurses5-dev libreadline6-dev \
        libgdbm-dev libgdbm-compat-dev liblzma-dev \
        wget ca-certificates \
        build-essential && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ARG PYTHON_VERSION
ENV PYTHON_VERSION ${PYTHON_VERSION}

COPY build-native.sh .
RUN wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
RUN bash build-native.sh

# Build cross Python

FROM ghcr.io/tttapa/toolchains:${HOST_TRIPLE} AS cross-build

ARG HOST_TRIPLE
ENV HOST_TRIPLE ${HOST_TRIPLE}

ARG PYTHON_VERSION
ENV PYTHON_VERSION ${PYTHON_VERSION}

USER root

COPY --from=native-build /opt/python-${PYTHON_VERSION} /
RUN test "$(python3 --version)" = "Python ${PYTHON_VERSION}"

COPY --from=native-build "/Python-${PYTHON_VERSION}.tgz" /

ENV TOOLCHAIN_PATH="/home/develop/opt/${HOST_TRIPLE}"
ENV PATH "$TOOLCHAIN_PATH/bin:$PATH"

COPY build-cross.sh .
RUN bash build-cross.sh

# Copy to clean image

FROM ubuntu:jammy

ARG HOST_TRIPLE
ENV HOST_TRIPLE ${HOST_TRIPLE}

ARG PYTHON_VERSION
ENV PYTHON_VERSION ${PYTHON_VERSION}

COPY --from=native-build /opt/python-${PYTHON_VERSION} /
COPY --from=cross-build /home/develop/opt /opt/x-tools/
COPY --from=cross-build /opt/${HOST_TRIPLE} /opt/${HOST_TRIPLE}
RUN ln -s python3-config /usr/local/bin/python-config && \
    ln -s python3 /usr/local/bin/python && \
    ln -s pip3 /usr/local/bin/pip
ENV PATH "/opt/x-tools/${HOST_TRIPLE}/bin:$PATH"
