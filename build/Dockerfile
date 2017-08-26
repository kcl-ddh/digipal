# To build DigiPal Framework Image with Docker:
#
# docker build -t gnoelddh/digipal build
#
# Then run the container like this:
#
# docker run -ti -p 80:80 gnoelddh/digipal
#
# Now you can browse to http://localhost/ from your host machine
# Note that this version is for local use only, not for production.
# You can use it to try out DigiPal or to start your own research.
#

FROM ubuntu:latest

ENV DP_WS_PORT 80

# Install Linux Packages in one go (best practice)
# Convention: one line per category (e.g. lessc, image server, database, ...)
#RUN apt-get update -y && apt-get install -y --no-install-recommends apt-utils \
RUN apt-get update -y && apt-get install -y \
    autoconf pkg-config libtool git \
    nodejs npm \
    libjpeg-dev libtiff-dev imagemagick \
    postgresql \
    python python-pip python-dev libxml2-dev libxslt1-dev libpq-dev \
    nginx uwsgi-plugin-python \
    supervisor wget vim \
&& apt remove -y python3.5 \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

#&& apt autoremove -y \

########################
# LESSC & TYPESCRIPT

RUN npm install -g less typescript; ln -s /usr/bin/nodejs /usr/bin/node

########################
# IMAGE PROCESSING

# download and build image server
# see https://github.com/ruven/iipsrv
# install dependencies (see above)

USER root

COPY build-iipsrv.sh /tmp/build-iipsrv.sh
RUN bash /tmp/build-iipsrv.sh

########################
# DATABASE
# see http://docs.docker.com/examples/postgresql_service/

USER postgres

# Create the database, the user and allow local and remote access using md5 auth.
# Fixes issue with Django accessing the DB
# Adjust PostgreSQL configuration so that remote connections to the database are possible.
RUN /etc/init.d/postgresql start &&\
        psql -c "CREATE USER app_digipal WITH PASSWORD 'dppsqlpass';" &&\
        createdb -E 'utf-8' -T template0 -O app_digipal digipal &&\
        sed -i 's/local\s*all\s*all\s*peer/local    all    all    md5/' $(psql -c "SHOW hba_file;" | grep conf | xargs) &&\
        echo "host all  all    0.0.0.0/0  md5" >> $(psql -c "SHOW hba_file;" | grep conf | xargs)

USER root

########################
# PYTHON + PIP
RUN pip install --upgrade pip

########################
# DIGIPAL FRAMEWORK

# Fetch Digipal
RUN mkdir /home/digipal

WORKDIR /home/digipal

# (inc. the number in echo to force docker build to fetch new version of the code)
RUN echo "5" && git clone -b develop https://github.com/kcl-ddh/digipal.git /home/digipal &&\
    ln -s local_settings.template.py digipal/local_settings.py

COPY * /home/digipal/build/

RUN echo "1" && pip install -r build/requirements.txt

# Create tables, admin and site records, indexes

RUN build/fix_permissions.sh

USER postgres

RUN /etc/init.d/postgresql start &&\
        python manage.py syncdb --noinput &&\
        python manage.py migrate &&\
        python manage.py loaddata build/data_init.json build/data_char.json build/data_menu.json build/data_test.json &&\
        python manage.py dpsearch index &&\
        python manage.py dpsearch index_facets
#        python manage.py collectstatic --noinput

USER root

# give files to www-data
#RUN chown -R www-data:www-data ../digipal && \
#    chmod -R ug+rw ../digipal && \
#    chmod -R o-rw ../digipal

########################
# WEB SERVER

RUN rm /etc/nginx/sites-enabled/default && ln -s /home/digipal/build/nginx.conf /etc/nginx/sites-enabled/digipal.conf

########################
# SUPERVISOR
RUN mkdir -p /var/log/supervisor

# Port for web server
EXPOSE 80

########################
# START-UP

ENV SHELL /bin/bash

VOLUME /home/digipal/digipal_project/

CMD ["/bin/bash", "/home/digipal/build/startup.sh"]
