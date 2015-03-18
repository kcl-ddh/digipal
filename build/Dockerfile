# To build DigiPal Framework Image with Docker:
#
# docker build -t digipal/framework build
#
# Then run the container like this:
#
# docker run -t -i -p 8080:8080 -p 8081:8081 -p 2222:22 digipal/framework
#
# Now you can browse to http://localhost:8080/ from your host machine
# Note that this version is for local use only, not for production.
# You can use it to try out DigiPal or to start your own research.
#

FROM ubuntu:latest

ENV DP_WS_PORT 8080

RUN apt-get update

########################
# DATABASE
# see http://docs.docker.com/examples/postgresql_service/
RUN apt-get -y install postgresql

USER postgres

# Create the database, the user and allow local and remote access using md5 auth.
# Fixes issue with Django accessing the DB
# Adjust PostgreSQL configuration so that remote connections to the database are possible.
RUN /etc/init.d/postgresql start &&\
        psql -c "CREATE USER app_digipal WITH PASSWORD 'dppsqlpass';" &&\
        createdb -E 'utf-8' -T template0 -O app_digipal digipal &&\
        sed -i 's/local\s*all\s*all\s*peer/local    all    all    md5/' $(psql -c "SHOW hba_file;" | grep conf | xargs) &&\
        echo "host all  all    0.0.0.0/0  md5" >> $(psql -c "SHOW hba_file;" | grep conf | xargs)

EXPOSE 5432

USER root

########################
# PROGRAMMING LANGUAGE
RUN apt-get -y install python python-pip python-dev libxml2-dev libxslt1-dev libpq-dev

########################
# DIGIPAL FRAMEWORK

# GIT
RUN apt-get -y install git

# Fetch Digipal
RUN mkdir /home/digipal

WORKDIR /home/digipal

# (inc. the number in echo to force docker build to fetch new version of the code)
RUN echo "11" && git clone https://github.com/kcl-ddh/digipal.git /home/digipal
RUN pip install -r build/requirements.txt

# Configure it
RUN cp digipal/local_settings.template.py digipal/local_settings.py

# Create tables, admin and site records, indexes
RUN /etc/init.d/postgresql start &&\
        python manage.py syncdb --noinput &&\
        python manage.py migrate &&\
        python manage.py loaddata build/data_init.json build/data_char.json build/data_menu.json build/data_test.json &&\
        python manage.py dpsearch index &&\
        python manage.py dpsearch index_facets

# Port for web server
EXPOSE 8080

########################
# IMAGE PROCESSING

# image conversion tool
RUN apt-get -y install imagemagick

# install web server for image server
RUN apt-get -y install lighttpd

# download and build image server
# see https://github.com/ruven/iipsrv
# install dependencies
RUN apt-get -y install autoconf libtool libjpeg-dev libtiff-dev
#
WORKDIR /root
RUN git clone https://github.com/ruven/iipsrv.git
WORKDIR /root/iipsrv
RUN ./autogen.sh && ./configure && make && cp src/iipsrv.fcgi /etc/lighttpd/

# configure web+image server
RUN cp /home/digipal/build/lighttpd-iipsrv.conf /etc/lighttpd/lighttpd.conf

WORKDIR /home/digipal

# Port for image server
EXPOSE 8081

########################
# SSH

RUN apt-get -y install openssh-server

# Allow ssh as root with password 'root'
RUN mkdir /var/run/sshd
RUN echo 'root:root' | chpasswd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

EXPOSE 22

########################
# START-UP

# Run the DB server, Web servers then a bash session
RUN echo "" > startup.sh
RUN echo "/etc/init.d/postgresql start" >> startup.sh
RUN echo "nohup python manage.py runserver 0.0.0.0:$DP_WS_PORT &" >> startup.sh
RUN echo "/etc/init.d/lighttpd start" >> startup.sh
RUN echo "/etc/init.d/ssh start" >> startup.sh
RUN echo "/bin/bash" >> startup.sh

CMD ["/bin/bash", "startup.sh"]
