cd /tmp
git clone https://github.com/ruven/iipsrv.git
cd iipsrv
# Deployed in /tmp/iipsrv/src/iipsrv.fcgi
./autogen.sh && ./configure && make
mv /tmp/iipsrv/src/iipsrv.fcgi /usr/local/bin/.
rm -rf /tmp/iipsrv
