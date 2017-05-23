/usr/bin/supervisord -c /home/digipal/build/supervisord.conf &
for i in {1..100}
do
  echo "try to connect to the site ($i)"
#  wget http://localhost:80 -t 1 -qO- &> /dev/null
  wget http://localhost:80 -t 1
  if [ "$?" -eq "0" ]; then
    break
  fi
  sleep 1
done
