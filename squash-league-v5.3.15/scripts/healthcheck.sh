#!/usr/bin/env sh
set -eu
curl -fsS "${1:-http://localhost}/api/health"
