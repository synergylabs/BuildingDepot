#!/bin/bash
set -e

# Generate bd_settings.cfg from template, substituting environment variables
envsubst < /app/configs/bd_settings.cfg.template > /app/configs/bd_settings.cfg

exec "$@"
