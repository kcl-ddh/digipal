#!/bin/sh
# DEPRECATED - USE SUPERVISORD instead
# Start The Image Server as a foreground process
# (use --background for daemon)
# See https://github.com/ruven/iipsrv#configuration
#
LOGFILE="/tmp/iipsrv.log"
VERBOSITY="1"
MAX_IMAGE_CACHE_SIZE="20"
JPEG_QUALITY="75"
MAX_CVT="800"
FILESYSTEM_PREFIX="/home/digipal/images/"

export LOGFILE
export VERBOSITY
export MAX_IMAGE_CACHE_SIZE
export JPEG_QUALITY
export MAX_CVT
export FILESYSTEM_PREFIX

#exec /etc/lighttpd/iipsrv.fcgi --bind 127.0.0.1:9000 --backlog 1024
# RUn as www-data... NOT WORKING!
#start-stop-daemon --start --background --make-pidfile --pidfile /var/run/iipsrv.pid  --chuid www-data --user www-data -v --umask 0 --exec /root/iipsrv/src/iipsrv.fcgi -- --bind 127.0.0.1:9000 --backlog 1024
# Run as root
# start-stop-daemon --start  --background --make-pidfile --pidfile /var/run/iipsrv.pid --user www-data --group www-data --exec /root/iipsrv/src/iipsrv.fcgi -- --bind 127.0.0.1:9000 --backlog 1024
/root/iipsrv/src/iipsrv.fcgi --bind 127.0.0.1:9000 --backlog 1024
