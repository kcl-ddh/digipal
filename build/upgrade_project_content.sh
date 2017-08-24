cd /home/digipal
# recreate content of digipal_project if empty (e.g. enabled volume in kitematic)
if [ ! -e "digipal_project/__init__.py" ]; then
    git checkout digipal_project
fi
# Upgrade imported project content into this version of Archetype
/etc/init.d/postgresql start && python manage.py collectstatic --noinput && python manage.py migrate --fake-initial && python manage.py migrate
# we don't need django/psql
/etc/init.d/postgresql stop
# reset permission to www-data
chown -R www-data:www-data ../digipal && chmod -R ug+rw ../digipal && chmod -R o-rw ../digipal
# grant permissions to share folder to world
chmod o+rw -R digipal_project

