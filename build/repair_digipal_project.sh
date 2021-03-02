# Scenario: user has enabled or changed the folder of the docker data volume.
# That's the content of digipal_project.
# This script repair the content of digipal_project, add the missing parts.
cd /home/digipal

# Recreate content of digipal_project if empty (e.g. enabled volume in kitematic)
if [ ! -e "digipal_project/__init__.py" ]; then
    # repair from github
    echo "RESTORE digipal_project from github"
    git checkout digipal_project

    if [ ! -e digipal_project/archetype.tar ]; then
        if [ ! -e "digipal_project/archetype.tar.gz" ]; then
            if [ -e "build/archetype.tar.gz" ]; then
                echo "RESTORE demo site"
                cp build/archetype.tar.gz digipal_project/.
            fi
        fi

        if [ -e "digipal_project/archetype.tar.gz" ]; then
            pushd digipal_project
            gunzip -f archetype.tar.gz
            popd
        fi
    fi

    if [ -e digipal_project/archetype.tar ]; then
        # TODO: restore archetype.zip under digipal_project
        echo "deploy digipal_project"
        rm -rf digipal_project/customisations digipal_project/templates digipal_project/static digipal_project/media digipal_project/images digipal_project/logs digipal_project/django_cache digipal_project/search
        tar -xf digipal_project/archetype.tar -C digipal_project
    fi
fi

# make sure static exists otherwise collectstatic will crash
if [ ! -e "digipal_project/static" ]; then
    mkdir digipal_project/static
fi

# configure and copy default DB into digipal_project
if [ ! -e "digipal_project/database" ]; then
    mkdir digipal_project/database
fi

PG_CONFIG_PATH=`find /etc -iname postgresql.conf`
PG_CONFIG_PATH_ORIGINAL="$PG_CONFIG_PATH.bk"
if [ ! -e "$PG_CONFIG_PATH_ORIGINAL" ]; then
    # make a copy of the original psql config file
    cp $PG_CONFIG_PATH $PG_CONFIG_PATH_ORIGINAL
    # psql data directory = digipal_project/database
    sed -i -E "s@data_directory.*@data_directory = '/home/digipal/digipal_project/database'@g" $PG_CONFIG_PATH
fi
# get the path the original data directory
PG_ORIGINAL_DATA_DIR=`grep 'data_directory' $PG_CONFIG_PATH_ORIGINAL | sed -E "s@data_directory.*=.*'(.*)'.*@\1@g"`

if [ ! -e "digipal_project/database/PG_VERSION" ]; then
    # database is missing, let's copy it from the original psql data dir
    rm -rf digipal_project/database/*
    cp -r $PG_ORIGINAL_DATA_DIR/* digipal_project/database/.
    # Create the database, the user and allow local and remote access using md5 auth.
    # Fixes issue with Django accessing the DB
    # Adjust PostgreSQL configuration so that remote connections to the database are possible.
    # RUN /etc/init.d/postgresql start &&\

    source build/fix_permissions.sh

    service postgresql start
    echo "RECREATE DATABASE"
    su postgres -c /bin/bash <<"EOF"
        psql -c "CREATE USER app_digipal WITH PASSWORD 'dppsqlpass';" &&\
        createdb -E 'utf-8' -T template0 -O app_digipal digipal &&\
        sed -i 's/local\s*all\s*all\s*peer/local    all    all    md5/' $(psql -c "SHOW hba_file;" | grep conf | xargs) &&\
        echo "host all  all    0.0.0.0/0  md5" >> $(psql -c "SHOW hba_file;" | grep conf | xargs)
EOF

    if [ -e "digipal_project/archetype.sql" ]; then
        echo "RESTORE DATABASE"
        chmod o+r digipal_project/archetype.sql
        chmod o+r -R build
        chmod o+xr -R build/restore_database.sh
        su -c build/restore_database.sh -s /bin/bash postgres
    fi

    service postgresql stop
fi

source build/fix_permissions.sh
