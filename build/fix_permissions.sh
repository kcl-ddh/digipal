# Reset the file permissions to keep www-data, postgres and docker host user
# happy. 
cd /home/digipal

# reset permission to www-data
chown -R www-data:www-data ../digipal
chmod -R ug+rw ../digipal
chmod -R o-rwx ../digipal

# grant permissions to project/shared folder to world
chmod o+rwx -R digipal_project
# needed for postgres to run sql scripts
chmod o+rwx -R build/schema_upgrades
chmod o+x build

# special permission requirements for psql on its database folder
chmod o+x .
chown postgres:postgres -R digipal_project/database
chmod u+rwx -R digipal_project/database
chmod go-rwx -R digipal_project/database
