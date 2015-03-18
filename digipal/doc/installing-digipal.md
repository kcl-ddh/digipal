# Installing DigiPal

Update (18/03/15): Docker is now the recommended way to install the DigiPal framework on your machine. The documentation below is therefore superceded by those found on the [DigiPal Docker page](https://registry.hub.docker.com/u/gnoelddh/digipal/).
 
## Installing DigiPal
Installing DigiPal is an advanced task doable by developers/experienced users only, as it requires certain software installed and some basic knowledge to set it up. Those without the require experience, should try installing the [virtual machine](/digipal/doc/virtual-machine.md) instead.

A basic requirement to install DigiPal is having [Python](https://www.python.org/) 2.6+ installed (we don't support Python 3). Almost all the Linux distributions and Mac OSX machine have it installed by default.

Windows users may find it at the address [https://www.python.org/download/windows/](https://www.python.org/download/windows/).

### Download DigiPal
Using GIT:You need to have git installed. On a Ubuntu/Debian system, you can do that by running the following command in your terminal:


```
sudo apt-get install git
```
For all the other versions, you can find them at the address [http://git-scm.com/downloads](http://git-scm.com/downloads)

 

The recommended way to download Digipal is to run this the following commands in your terminal: 


```
git clone https://github.com/kcl-ddh/digipal
```
Unless you are a software developer who wants to contribute to DigiPal code base you'll need to switch to the latest stable version:


```
git checkout v1.0
```
Where v1.0 is the version you want to install. For newer versions please regularly consult the [DigiPal releases page](https://github.com/kcl-ddh/digipal/releases).

ZIP:
```
Alternatively, you can download the project ZIP folder at the address [https://github.com/kcl-ddh/digipal/archive/master.zip](https://github.com/kcl-ddh/digipal/archive/master.zip).
```

### Installing Requirements
Using PIP:Before installing the requirements, please make sure you have the following packages already installed:


* python-dev
* postgresql-9.3
* postgresql-server-dev-9.3
* libmysqlclient-dev

After that, run in the terminal the following command:




```
pip install -r requirements.txt
```
To see or manually install all the requirements, consult the requirements.txt file provided in the _doc_ folder.

### 

### Database
**In order to run the DigiPal Database we used a [PostgreSQL](http://www.postgresql.org/) database server. Therefore, we recommend you to use PostgreSQL as well since we cannot ensure that the database will work on other database management systems.**

First you'll need to create an empty database, a database user and grant that user permissions on that database. You can do that with the [PgAdmin ](http://www.pgadmin.org/)user interface or from the command line. Either way you'll need sufficient privilege on the database system to carry out those operations. If you've installed PosgreSQL yourself then you can use the 'posgres' user and the its password to access the database shell:


```
psql -U postgres
```

```
create database YOUR_DATABASE_NAME;
```

```
create user A_USER_NAME with password 'A_PASSWORD';
```

```
grant all privileges on database YOUR_DATABASE_NAME to A_USER_NAME;
```

```
\q
```
Set up the database in your local_settings.py file and fill the DATABASES object with your settings:


```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'YOUR_DATABASE_NAME',
        'USER': 'A_USER_NAME',
        'PASSWORD': 'A_PASSWORD',
        'HOST': 'localhost',
        'PORT': '',
    }
 }

```
After that, run in your terminal the following commands:


```
python manage.py syncdb
python manage.py migrate 
```

```
python manage.py collectstatic --noinput
```

## Running DigiPal
By using the system terminal, go to your DigiPal root folder, and then run:


```
python manage.py runserver

```
Run you browser at the address [http://](http://localhost:8000/)[localhost:8000](http://localhost:8000/)

_Giancarlo Buomprisco _

