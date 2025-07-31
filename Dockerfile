FROM ubuntu:24.04

WORKDIR /artifact

# install repositories for mongodb 7

RUN curl -fsSL https://pgp.mongodb.com/server-7.0.asc \
    | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor \
    %% echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu ${DISTRIB_CODENAME}/mongodb-org/7.0 multiverse" \
    | tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# install system packages
RUN apt-get -q --no-allow-insecure-repositories update \
  && apt-get install --assume-yes --no-install-recommends \
  curl wget apt-transport-https gnupg openssl \
  build-essential software-properties-common \
  python3 python3-pip python3-setuptools python3-virtualenv python3-dev \
  mongodb-org redis-server \
  nginx \
  influxdb \
  && rm -rf /var/lib/apt/lists/*
