from fabric.api import *
from fabric.utils import puts
from fabric.utils import fastprint
from fabric.contrib.files import *
from fabric.contrib.project import rsync_project
from fabric.contrib.project import upload_project
from contextlib import contextmanager as _contextmanager
import os

# TODO apt-get requirements!

# Hosts to deploy to
env.hosts = ["localhost"]
#env.hosts = ["gitlab"]

# Where your project code lives on the local machine
env.project_root = "/home/robbie/work/nmap_tool/nwsdb"
env.project_name = "nwsdb"

# Where the static files get collected locally. Your STATIC_ROOT setting.
### pretty, pretty please.. call your STATIC_ROOT "static"
# env.local_static_root = "/home/robbie/work/nmap_tool/nwsdb/static_for_prod"

# Where the static files should go remotely
env.remote_root = "/var/www/site_nwscandb"

# make sure there is no trouble with forgotten trailing slashes
LOCAL_ROOT = os.path.dirname(os.path.join(env.project_root, ''))
### pretty, pretty please.. call your STATIC_ROOT "static"
LOCAL_STATIC_DIR_NAME = "static"

REMOTE_ROOT = os.path.dirname(os.path.join(env.remote_root, ''))
#REMOTE_DIR_PROJECT = os.path.join(REMOTE_ROOT, env.project_name)
#REMOTE_DIR_VENV = os.path.join(REMOTE_ROOT, "venv/")


def remove_dest_dir(dest_dir):
    if exists(dest_dir):
        sudo("rm -rf {0}".format(dest_dir))

def clean_up_remote(dest_dir):
    remove_dest_dir("{0}/nwsdb/.git".format(dest_dir))
    remove_dest_dir("{0}/nwsdb/common-static".format(dest_dir))
    remove_dest_dir("{0}/nwsdb/fabfile.py".format(dest_dir))
    remove_dest_dir("{0}/nwsdb/fabfile.pyc".format(dest_dir))
    remove_dest_dir("{0}/nwsdb/nwscandb/settings_dev.py".format(dest_dir))
    remove_dest_dir("{0}/nwsdb/nwscandb/settings_dev_secret.py".format(dest_dir))

def deploy_static(local_dir, dest_dir):
    with cd(env.project_root):
        # TODO hard coded python for manage.py?!
        local("/home/robbie/work/nmap_tool/venv/bin/python manage.py collectstatic -v0 --noinput")
        local_static_dir_abs = os.path.join(local_dir, LOCAL_STATIC_DIR_NAME)
        upload_project(local_static_dir_abs, dest_dir, use_sudo=True)
        local("rm -rf {0}".format(LOCAL_STATIC_DIR_NAME))

def deploy_app(local_dir, dest_dir):
    upload_project(local_dir, dest_dir, use_sudo=True)

def chown_dir(dest_dir, user):
    sudo("chown -R {0}:{0} {1}".format(user, dest_dir))

def venv_deploy(dest_dir):
    sudo("virtualenv -p /usr/bin/python3.4 {0}/venv".format(dest_dir))

def venv_install_requirements(dest_dir):
    with settings(sudo_user=env.user):
        run("{0}/venv/bin/pip install -U pip".format(dest_dir))
        run("{0}/venv/bin/pip install -U -r {0}/nwsdb/requirements.txt".format(dest_dir))

def deploy_all(local_root=LOCAL_ROOT, remote_root=REMOTE_ROOT):
    #
    puts("--- Deploying from this host to \"{0}\" as {1}  ---".format(env.host, env.user))

    remove_dest_dir(remote_root)
    sudo("mkdir -p {0}".format(remote_root))
    deploy_static(local_root, remote_root)
    deploy_app(local_root, remote_root)

    venv_deploy(remote_root)
    chown_dir(remote_root, user=env.user)
    venv_install_requirements(remote_root)
    chown_dir(remote_root, user="www-data")

    sudo("cp {0}/nwsdb/nwscandb_prod.conf /etc/apache2/sites-available/".format(remote_root))
    sudo("a2ensite nwscandb_prod")
    sudo("service apache2 reload")


def sync_project(local_root=LOCAL_ROOT, remote_root=REMOTE_ROOT):
    puts("--- Sync from \"{0}\" to {1}  ---".format(local_root, remote_root))
    chown_dir(remote_root, user=env.user)
    rsync_project(remote_root, local_root, exclude="nwsdb/.git")
    chown_dir(remote_root, user="www-data")
    clean_up_remote(remote_root)
    sudo("touch {0}/nwsdb/nwscandb/wsgi_prod.py".format(remote_root))


def testing():
    pass

