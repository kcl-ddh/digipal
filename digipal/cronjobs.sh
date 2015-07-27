#!/bin/bash
# Runs regular tasks

env_path="$1"

DIR_PRJ=$( cd "$( dirname "$0" )" && pwd )/..
cd $DIR_PRJ

if [ -n "$env_path" ]
    then
        source $env_path/bin/activate
fi

# Reindexing
python manage.py dpsearch index
python manage.py dpsearch index_facets --if=manuscripts,images,scribes,hands,texts

deactivate
