#!/usr/bin/env bash
exec "$(cd "$(dirname "$0")" && pwd)/launcher/build_launcher.sh" "$@"
