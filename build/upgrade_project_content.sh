# Scenario: user has copied content from other Archetype instance into 
# digipal_project. This script tried to upgrade that content.
cd /home/digipal

source build/repair_digipal_project.sh

# Upgrade imported database to this version of Archetype
service postgresql start
python manage.py migrate --fake-initial --no-initial-data --noinput
python manage.py migrate --no-initial-data --noinput
# make sure upgraded files are always copied (-c, so ignore misleading timestamps)
python manage.py collectstatic -c --noinput >> digipal_project/logs/docker.log
if [ ! -e "digipal_project/search/faceted" ]; then
    source build/fix_permissions.sh
    su www-data -s /bin/bash -c "python manage.py dpsearch index_facets"
fi
if [ ! -e "digipal_project/search/unified" ]; then
    source build/fix_permissions.sh
    su www-data -s /bin/bash -c "python manage.py dpsearch index"
fi
service postgresql stop

source build/fix_permissions.sh
