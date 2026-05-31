FROM frappe/erpnext-worker:version-15

ARG DEBIAN_FRONTEND=noninteractive

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    curl \
    git \
    jq \
    libffi-dev \
    libssl-dev \
    nano \
    vim \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir devcontainer-cli

USER frappe

WORKDIR /workspace/lenscloud
