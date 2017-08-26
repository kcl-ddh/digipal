# Scenario: user has copied content from other Archetype instance into 
# digipal_project. This script tried to upgrade that content.
cd /home/digipal

source build/repair_digipal_project.sh

# Upgrade imported database to this version of Archetype
service postgresql start
python manage.py migrate --fake-initial
python manage.py migrate
python manage.py collectstatic --noinput >> digipal_project/logs/docker.log
service postgresql stop

source build/fix_permissions.sh
