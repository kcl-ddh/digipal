# Reset the file permissions to keep www-data, postgres and docker host user
# happy. 
cd /home/digipal

# reset permission to www-data
chown -R www-data:www-data ../digipal
chmod -R ug+rw ../digipal
chmod -R o-rwx ../digipal

# grant permissions to project/shared folder to world
chmod o+rw -R digipal_project
chmod o+x digipal_project

# special permission requirements for psql on its database folder
chown postgres:postgres -R digipal_project/database
chmod u+rw -R digipal_project/database
chmod u+x digipal_project/database
chmod go-rwx digipal_project/database
