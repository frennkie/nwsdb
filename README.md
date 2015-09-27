# nmap-webgui

## Code status

This project is a fork of this repo: https://github.com/savon-noir/nmap-webgui

For in Progress

## Backup/Restore

mongodump

mongorestore --db nmapuidb --collection reports dump/nmapuidb/reports.bson
mongorestore --db nmapuidb --collection celery_taskmeta dump/nmapuidb/celery_taskmeta.bson

## clean out all reports

mongo nmapuidb
db.reports.remove({})
db.celery_taskmeta.remove({})

## Use cases
nmap-webgui is a multi-user small web application based on flask to enable the user to:

- launch nmap scans (DONE)
- schedule periodic scans
- review scan reports
- diff and compare scan reports
- display stats of scan reports

nmap-webgui is relying on the following technologies:

- flask
- celery
- rabbitmq
- mongodb
- python-libnmap

## Dependencies

Following packages need to be installed:

- flask via pip
- flask-login via pip
- flask-pymongo via pip
- flask-scripts via pip (optional)
- rabbitmq server (no specific config needed)
- mongodb daemon (to store users data and celery tasks)

##Quick install

This is a draft on how to install and run nmap-webgui:

```bash
    # install packages in a virtualenv or whatever
    $ pip install Flask
    $ pip install Flask-Login
    $ pip install Flask-PyMongo
    $ pip install Flask-Script
    # for celery, ensure you are running chiastic slide (version > 3)
    $ pip install celery

    # install mongodb and rabbitmq (the way you want it)
    $ yum install mongod
    $ yum install mongod-server
    $ yum install rabbitmq-server

    # start rabbitmq and mongodb
    $ service mongod start
    $ service rabbitmq-server start

    # install nmap
    $ yum install nmap

    # install python-libnmap
    $ git clone https://github.com/savon-noir/python-libnmap.git
    $ cd python-libnmap
    $ python setup.py install

    # install the webgui
    $ git clone https://savon_noir@bitbucket.org/savon_noir/nmap-webgui.git
    $ cd nmap-webgui
    $ python setup.py install

    # run celery
    $ celery -A nmapui.tasks worker --loglevel=debug

    # add a user, start the web app in debug and login
    $ python manage.py adduser <username> <email>
    $ python manage.py runserver
```
