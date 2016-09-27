# DEPRECATED - REPLACED BY SUPERVISORD
# SEE build/supervisord.conf
#
# Docker CMD startup script
# Starts services (DB, Web, Image server)

cd /home/digipal

/etc/init.d/postgresql start

sh /home/digipal/build/iipsrv.sh

# RUN echo "nohup python manage.py runserver 0.0.0.0:$DP_WS_PORT &" >> startup.sh
uwsgi --ini /home/digipal/digipal/wsgi.template.ini

/etc/init.d/nginx start

/bin/bash
