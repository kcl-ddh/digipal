#
# To build DigiPal Framework Image with Docker
#
# sudo docker build -t digipal/framework digipal
#

FROM ubuntu:latest

# WORK IN PROGRESS...

RUN apt-get update

########################
# DATABASE
# see http://docs.docker.com/examples/postgresql_service/
RUN apt-get -y install postgresql

USER postgres

RUN /etc/init.d/postgresql start &&\
        psql -c "CREATE USER app_digipal WITH PASSWORD 'dppsqlpass';" &&\
        createdb -O app_digipal digipal

# Fixes issue with Django accessing the DB
sed 's/local\s*all\s*all\s*peer/local    all    all    md5/' /etc/postgresql/9.3/main/pg_hba.conf

# Adjust PostgreSQL configuration so that remote connections to the
# database are possible.
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/9.3/main/pg_hba.conf

EXPOSE 5432

#CMD ["/usr/lib/postgresql/9.3/bin/postgres", "-D", "/var/lib/postgresql/9.3/main", "-c", "config_file=/etc/postgresql/9.3/main/postgresql.conf"]

USER root

########################
# PROGRAMMING LANGUAGE
RUN apt-get -y install python python-pip python-dev libxml2-dev libxslt1-dev libpq-dev

########################
# Framework

# GIT
RUN apt-get -y install git

# Fetch Digipal
RUN mkdir /home/digipal
RUN echo "1" && git clone https://github.com/kcl-ddh/digipal.git /home/digipal
RUN pip install -r /home/digipal/doc/requirements.txt

# Configure it
RUN cp /home/digipal/digipal/local_settings.template.py /home/digipal/digipal/local_settings.py

########################
# START-UP
RUN cd

RUN echo "/etc/init.d/postgresql start" > /root/startup.sh
RUN echo "/bin/bash" >> /root/startup.sh


CMD ["/bin/bash", "/root/startup.sh"]
