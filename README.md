

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

