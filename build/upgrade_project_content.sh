cd /home/digipal

# Recreate content of digipal_project if empty (e.g. enabled volume in kitematic)
if [ ! -e "digipal_project/__init__.py" ]; then
    git checkout digipal_project
fi

source build/fix_permissions.sh

# Upgrade imported database to this version of Archetype
service postgresql start
python manage.py collectstatic --noinput
python manage.py migrate --fake-initial
python manage.py migrate
/etc/init.d/postgresql stop

source build/fix_permissions.sh
