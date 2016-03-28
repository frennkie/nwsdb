

https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-14-04
https://help.ubuntu.com/community/PostgreSQL

sudo apt-get update
sudo apt-get install postgresql postgresql-server-dev-9.4
 postgresql-contrib 

sudo -i -u postgres


psql

\q

createuser --interactive
Enter name of role to add: nwscandb
Shall the new role be a superuser? (y/n) n
Shall the new role be allowed to create databases? (y/n) y
Shall the new role be allowed to create more new roles? (y/n) n


createdb nwscandb



Project directory layout

Project Name: nwscandb
(Web)Site Name: nwscandb   ( could also be www.example.com )

tree /var/www/site_nwscandb/ -L 2
/var/www/site_nwscandb/        # website_root
├── nwsdb                    # this should be the project name (nwscandb)! 
│   ├── accounts
│   ├── CHANGELOG.md
│   ├── dbimport
│   ├── insert.sql
│   ├── manage.py
│   ├── multidns
│   ├── nmap
---
/var/www/site_nwscandb/nwsdb/nwscandb
        ├── celery.py
        ├── __init__.py
        ├── ldap_auth.py
        ├── settings_basic.py
        ├── settings_dev.py
        ├── settings_dev_secret.py        
        ├── settings_prod.py
        ├── settings_prod_secret.py
        ├── urls.py
        ├── wsgi_dev.py
        └── wsgi_prod.py
---
│   ├── nwscandb_dev.conf
│   ├── nwscandb_prod.conf
│   ├── README.md
│   ├── requirements.txt
│   └── Vagrantfile
├── static
│   ├── accounts
│   ├── admin
│   ├── css
│   ├── django_extensions
│   ├── fonts
│   ├── js
│   ├── mptt
│   └── rest_framework
└── venv
    ├── bin
    ├── djcelery
    ├── include
    ├── lib
    ├── pip-selfcheck.json
    └── share






### Get started

https://django.readthedocs.org/en/1.8.x/intro/tutorial01.html

##### Create project (overall frame)
```
django-admin startproject nwscandb
```

##### Setup basic settings (e.g. database credentials)
```
vi nwscandb/settings.py
vi nwscandb/my.cnf
```

##### Apply basic settings (e.g. populate db)
```
python manage.py migrate
```

##### Create app (a project can have multiple apps)
```
python manage.py startapp nmap
```

##### Database migrations

###### Create
`python manage.py makemigrations nmap`

##### (optional: View)
`python manage.py sqlmigrate nmap 0001

###### Apply
`python manage.py migrate`



#### Dev environment


###### ipython

https://opensourcehacker.com/2014/08/13/turbocharge-your-python-prompt-and-django-shell-with-ipython-notebook/
```
pip install django_extensions
pip install ipython
```

Beware (a lot) - needed for --notebook
```
pip install jupyter
pip install IPython
```

Add django_extensions to Django settings INSTALLED_APPS list:
```
INSTALLED_APPS = (
     ....
    'django_extensions'
)
```



```
python manage.py shell_plus
# or
python manage.py shell_plus --notebook
```

Autoreload (careful!)
```
%load_ext autoreload
%autoreload 2
```

##### Schema Graph
```
./manage.py graph_models auth nmap  -g -o my_project_visualized.png
```

