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
# DIGIPAL FRAMEWORK

# Fetch Digipal
RUN mkdir /home/digipal

WORKDIR /home/digipal

# (inc. the number in echo to force docker build to fetch new version of the code)
RUN echo "11" && git clone -b develop https://github.com/kcl-ddh/digipal.git /home/digipal

COPY * build/

########################
# DATABASE
# see http://docs.docker.com/examples/postgresql_service/
# move psql data directory inside digipal_project
RUN bash build/repair_digipal_project.sh

########################
# PYTHON + PIP
RUN pip install --upgrade pip

########################
# DIGIPAL FRAMEWORK

RUN echo "1" && pip install -r build/requirements.txt

# Create tables, admin and site records, indexes

RUN build/fix_permissions.sh

RUN /etc/init.d/postgresql start &&\
        python manage.py migrate &&\
        python manage.py loaddata build/data_init.json build/data_char.json build/data_menu.json build/data_test.json &&\
        python manage.py dpsearch index &&\
        python manage.py dpsearch index_facets

USER root

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
