# Docker CMD startup script
# Starts services (DB, Web, Image server)
# Wait until site is running

/usr/bin/supervisord -c /home/digipal/build/supervisord.conf &
for i in {1..200}
do
  echo "try to connect to the site ($i)"
  wget http://localhost:80 -t 1 -qO- &> /dev/null
  if [ "$?" -eq "0" ]; then
    echo "=================="
    echo "WEBSITE IS RUNNING"
    echo "=================="
    sleep infinity
    break
  fi
  sleep 1
done

echo "WEBSITE IS *NOT* RUNNING"
