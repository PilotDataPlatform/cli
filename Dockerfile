FROM indocpilot.azurecr.io/base-image/python:3.10.15-v1 AS base-image

ARG CLI_VERSION

RUN addgroup --system indoc && \
    useradd --gid indoc --system --shell /bin/bash indoc

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        curl

RUN curl -L https://github.com/PilotDataPlatform/cli/releases/download/${CLI_VERSION}/pilotcli_cloud \
    --output /usr/local/bin/pilotcli

RUN chmod +x /usr/local/bin/pilotcli
