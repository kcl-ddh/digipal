# Docker CMD startup script
# Starts services (DB, Web, Image server)
# Wait until site is running

echo "------------------------------"
echo "STARTING CONTAINER..."

function on_stop_container {
    echo "Stopping container..."
    echo "Stopping container..." >> /home/digipal/digipal_project/logs/docker.log
    chmod o+rwx -R /home/digipal/digipal_project
    kill -s TERM `cat /home/digipal/supervisord.pid`
    echo "------------------------------"
}

trap "on_stop_container" SIGTERM

source /home/digipal/build/upgrade_project_content.sh

/usr/bin/supervisord -c /home/digipal/build/supervisord.conf &
for i in {1..200}
do
  echo "waiting for site... ($i)"
  wget http://localhost:80 -t 1 -qO- &> /dev/null
  if [ "$?" -eq "0" ]; then
    cat /home/digipal/digipal/__init__.py
    echo "=================="
    echo "WEBSITE IS RUNNING"
    echo "=================="
    # sleep infinity is not trappable
    while true; do sleep 1 || break; done
    break
  fi
  sleep 1 || break
done
# sleep infinity is not trappable
while true; do sleep 1 || break; done

echo "WEBSITE IS *NOT* RUNNING"
