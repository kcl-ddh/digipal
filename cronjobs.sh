#!/bin/bash
# Runs regular tasks 

DIR_PRJ=$( cd "$( dirname "$0" )" && pwd )/..
DIR_ACTIVATE=../envs/digipal-dev/bin/activate
cd $DIR_PRJ
source $DIR_ACTIVATE

# Reindexing
python manage.py dpsearch index

deactivate
