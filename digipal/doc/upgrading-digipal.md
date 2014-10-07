# Upgrading DigiPal
 
## Introduction
The DigiPal framework is an open source project under continuous development. New versions with bug fixes and new features are released regularly on the [GitHub](https://github.com/kcl-ddh/digipal) website.

**We recommend that you always use the latest stable version of the code** rather than the current development version. The development version (labeled '**master**') is for software developers only. To install the latest stable version, go to the [DigiPal release page](https://github.com/kcl-ddh/digipal/releases) and look at the highest version number, then click that number to see the release notes, if any. We recommend you use git tools from the command line to clone and checkout that particular version on your machine.

When a new version is released you can follow the steps below to upgrade your own copy of the framework. All the computer commands mentioned below are executed in the shell/console from your project directory (the directory that contains the file 'manage.py'). To check which version you are running: 


```
git describe --tags
```
Alternatively you can also use this command:


```
python manage.py version
```

## Backing up your database
The first thing to do it is to back up your database. If anything goes wrong during the upgrade you can always roll back the changes and return to the previous state of your system.


```
python manage.py dpdb backup NAME
```
Where NAME is the name you want to give to your backup file. The script will ask you for the database password then will save the database into a single .sql file. 

## Upgrading the code

```
git fetch
```
Then list all available versions to see which one is the most recent: 


```
git tag
```
And upgrade your code to that version:


```
git checkout VERSION
```
Where VERSION is the new version you want to get.

However if you are a software developer and want to run the latest development version, you can run this command instead:


```
git checkout master
```

## Additional upgrade steps
The upgrade may contain important additional steps to be carried out now. Please check the release notes for the [version you are upgrading to on github](https://github.com/kcl-ddh/digipal/releases).

## Upgrading your database schema

```
python manage.py migrate
```

## Upgrading your media files

```
python manage.py collectstatic --noinput
```
Restarting your web server


```
python manage.py runserver 80
```
Where 80 is the port you want the server to run on.

## Restoring a backup
If something went wrong and you want to restore your system to how it was before the upgrade, first downgrade your code to the version you had before then restore your database:


```
python dbshell   (this command will ask you for the database password)
```

```
\i digipal/backups/NAME.sql
```

```
\q
```
Where NAME is the name of your backup file.

Restore all the media files:


```
python manage.py collectstatic --noinput
```
Restart your web server:


```
python manage.py runserver 80
```
 

_Geoffroy Noel_

