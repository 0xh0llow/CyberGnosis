#!/usr/bin/env bash

set -euo pipefail

# Compose v2 may route builds through buildx bake, which has caused
# intermittent failures such as "failed to execute bake: read |0: file
# already closed" on some Docker installations. Default to the classic
# compose builder unless the caller explicitly opts back in.
export COMPOSE_BAKE="${COMPOSE_BAKE:-false}"

if command -v docker-compose >/dev/null 2>&1; then
    exec docker-compose "$@"
fi

exec docker compose "$@"
