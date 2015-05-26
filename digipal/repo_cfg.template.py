# config file for repo.py

# The linux user group the files should belong to.
# Value is not used on Windows.
PROJECT_GROUP = 'digipal'

# The digipal app is always needed. By default it can be used as the main/project app.
# Set the following to True if the main app is the digipal app.
SELF_CONTAINED = True

# Set this to True is you are running the site using Django Web Server
# In that case collectstatic won't be run
DJANGO_WEB_SERVER = False
