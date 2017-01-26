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

# Set to True if you are editing the code with eclipse. 
# Eclipse needs the files to be writable by the owner
# even if the user editing has group write!
ECLIPSE_EDITABLE = False

# Set to True if www-data manages the code upgrade
# WWW-DATA will have write access to source code
# NOT FOR PRODUCTION SERVER
BUILT_BY_WWW_DATA = False

# Users with sudo access on this machine
# Used to fix file permissions
SUDO_USERS = ['gnoel', 'jeff']
