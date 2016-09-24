# Docker CMD startup script
# Starts services (DB, Web, Image server)
cd /home/digipal
/etc/init.d/postgresql start
# RUN echo "nohup python manage.py runserver 0.0.0.0:$DP_WS_PORT &" >> startup.sh
# RUN echo "/etc/init.d/lighttpd start" >> startup.sh
# RUN echo "/etc/init.d/ssh start" >> startup.sh
sh /home/digipal/build/iipsrv.sh
uwsgi --ini /home/digipal/digipal/wsgi.template.ini
/etc/init.d/nginx start

/bin/bash
