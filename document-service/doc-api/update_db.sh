#! /bin/sh
COMMAND=${1:-upgrade}
REVISION=${2:-}
echo starting $COMMAND $REVISION
export DEPLOYMENT_ENV=migration
cd /code
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
export FLASK_APP=wsgi:app
flask db $COMMAND $REVISION
echo 'upgrade completed'
