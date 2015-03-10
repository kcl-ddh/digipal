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

# Adjust PostgreSQL configuration so that remote connections to the
# database are possible.
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/9.3/main/pg_hba.conf

EXPOSE 5432

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
RUN git clone https://github.com/kcl-ddh/digipal.git /home/digipal
RUN pip install -r /home/digipal/doc/requirements.txt

########################
# START-UP
RUN cd

RUN echo "/etc/init.d/postgresql start" > /root/startup.sh
RUN echo "/bin/bash" >> /root/startup.sh


CMD ["/bin/bash", "/root/startup.sh"]
