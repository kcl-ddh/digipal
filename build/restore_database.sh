# Restore digipal_project/archetype.sql.
# This script MUST be executed as postgres user.

psql --quiet digipal < digipal_project/archetype.sql > /dev/null

# give all permissions to app_digipal
psql -c 'ALTER DATABASE digipal OWNER TO app_digipal;'
for table in `psql -tc "select tablename from pg_tables where schemaname = 'public';" digipal` ; do psql -c "alter table public.${table} owner to app_digipal" digipal ; done

# Special case for pre-django 1.7 database.
# python migrate --fake-initial cannot run straight after import 
# otherwise it will fail on existing tables (b/c some do not exists
# so django doesnt fake anything). We can't run it before either
# as the django migrations create records that will conflict with 
# database.
if ! grep 'django_migrations' digipal_project/archetype.sql; then
    # TODO: test if v1.2.2, we don't support v1.0 (yet)
    echo "Pre Django 1.7 database"
    if grep -n '0089_auto__chg' digipal_project/archetype.sql; then
        echo "UPGRADE DB from 1.2.2"
        psql --quiet digipal < build/schema_upgrades/1.2.2.sql > /dev/null
    else
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "!! ERROR: DATABASE CANNOT BE UPGRADED YET  !!"
        echo "!! DigiPal Docker v1.0                     !!"
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        # just run:
        # migrate --fake-initial
        # migrate --fake digipal 0002
        # migrate --fake-initial digipal
        # migrate --fake-initial digipal_text
        # migrate
        # run 1.2.1.sql (keyval table only)
    fi
fi
