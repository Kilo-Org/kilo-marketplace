FROM mcr.microsoft.com/devcontainers/base:jammy AS base

ARG PYTHON_VERSION=3.13

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

ENV UV_LINK_MODE="copy"
ENV UV_PYTHON=${PYTHON_VERSION}
COPY --from=ghcr.io/astral-sh/uv:0.10.2 /uv /uvx /bin/
RUN uv python install ${PYTHON_VERSION}
