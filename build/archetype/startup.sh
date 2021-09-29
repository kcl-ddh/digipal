# WIP! django startup for the docker-compose version of archetype
echo "Django project setup"
/bin/bash /home/digipal/build/upgrade_project_content.sh
echo "Start Django Uwsgi web service"
/usr/bin/uwsgi --ini /home/digipal/build/wsgi.ini
echo "End Django Uwsgi web service"
