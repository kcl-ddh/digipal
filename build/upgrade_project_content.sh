# Upgrade imported project content into this version of Archetype
cd /home/digipal
python manage.py colectstatic --noinput
python manage.py migrate --fake-initial
python manage.py migrate
