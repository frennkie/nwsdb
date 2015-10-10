# nwscandb

## Name

What does nwscandb stand for?
Possibly:
* Nmap Web Scan DB or
* NetWork Scan DB or
* something else


## Code status

Alpha.. just a bit more that POC.. but work in progess.. :-)


## Attribution

This project is based on the design and code writen by
https://github.com/savon-noir for the (in his terms) "Proof-of-Concept":
nmap-webgui currently located at https://github.com/savon-noir/nmap-webgui.

Big parts of the code and components were upgraded, changed out or removed
but some of the core is still present and especially this project still makes
heavy use of the python-libnmap library (also by savon-noir) which is
absolutely awesome.


## Main components
- flask
- celery
- mysql
- rabbitmq
- python-libnmap
- jQuery
- Bootstrap

## Dependencies

For anything you can (and need to) get from pip please check requirements.txt
file

Following system packages need to be installed:

- rabbitmq server (no specific config needed)
- mysql


##Quick install

This is a draft on how to install and run nwsdb:

```bash
# install packages in a virtualenv or whatever
virtualenv venv
source venv/bin/activate

pip install -U pip
pip install -U requirements.txt

# install mongodb and rabbitmq (the way you want it)
apt-get install mysql-server
aptg-et install rabbitmq-server

# start rabbitmq and mongodb
service mysqld start
service rabbitmq-server start

# install nmap
apt-get install nmap

# install python-libnmap
git clone https://github.com/savon-noir/python-libnmap.git
cd python-libnmap
python setup.py install

# install the nwsdb
???

# Update configuration (config.py)


```
# Database setup
```
CREATE DATABASE nwscandb;
GRANT ALL PRIVILEGES ON nwscandb.* TO nwscandb@localhost IDENTIFIED BY 'password';
FLUSH PRIVILEGES;

```

# run celery
```
celery -A nwscandb.tasks worker --loglevel=debug
```

# add a admin start the web app in debug and login
```

python manage.py add_admin <username> <email>
python manage.py runserver -p 80
```
