#! /bin/sh
echo 'starting upgrade'
export DEPLOYMENT_ENV=migration
uv run flask db upgrade