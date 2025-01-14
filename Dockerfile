FROM ubuntu:24.04

ARG CLI_VERSION
ARG CLI_OS

RUN apt-get update \
     && apt-get install -y curl;

RUN curl -L https://github.com/PilotDataPlatform/cli/releases/download/${CLI_VERSION}/pilotcli_${CLI_OS} \
    --output /usr/local/bin/pilotcli

RUN chmod +x /usr/local/bin/pilotcli

RUN pilotcli
