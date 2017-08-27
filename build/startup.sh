# Docker CMD startup script
# Starts services (DB, Web, Image server)
# Wait until site is running

function on_stop_container {
    echo "Stopping container..."
    chmod o+rwx -R /home/digipal/digipal_project
}

trap "on_stop_container" SIGTERM

source /home/digipal/build/upgrade_project_content.sh

/usr/bin/supervisord -c /home/digipal/build/supervisord.conf &
for i in {1..200}
do
  echo "waiting for site... ($i)"
  wget http://localhost:80 -t 1 -qO- &> /dev/null
  if [ "$?" -eq "0" ]; then
    echo "=================="
    echo "WEBSITE IS RUNNING"
    echo "=================="
    sleep infinity
    break
  fi
  sleep 1 || break
done
sleep infinity

echo "WEBSITE IS *NOT* RUNNING"
