from fabric.api import *
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
#REMOTE_DIR_APP = os.path.join(REMOTE_ROOT, "nwscandb/")
#REMOTE_DIR_VENV = os.path.join(REMOTE_ROOT, "venv/")


def remove_dest_dir(dest_dir):
    if exists(dest_dir):
        sudo("rm -rf {0}".format(dest_dir))

def deploy_static(local_dir, dest_dir):
    with cd(env.project_root):
        # TODO hard coded python for manage.py?!
        local("/home/robbie/work/nmap_tool/venv/bin/python manage.py collectstatic -v0 --noinput")
        local_static_dir_abs = os.path.join(local_dir, LOCAL_STATIC_DIR_NAME)
        upload_project(local_static_dir_abs, dest_dir, use_sudo=True)
        local("rm -rf {0}".format(LOCAL_STATIC_DIR_NAME))

def deploy_app(local_dir, dest_dir):
    upload_project(local_dir, dest_dir, use_sudo=True)

def chown_dir(dest_dir, user="www-data"):
    sudo("chown -R {0}:{0} {1}".format(user, dest_dir))

def venv_deploy(dest_dir):
    sudo("virtualenv -p /usr/bin/python3.4 {0}/venv".format(dest_dir))

def venv_install_requirements(dest_dir):
    with settings(sudo_user="robbie"):
        run("{0}/venv/bin/pip install -U pip".format(dest_dir))
        run("{0}/venv/bin/pip install -U -r {0}/nwsdb/requirements.txt".format(dest_dir))

def deploy_all(local_root=LOCAL_ROOT, remote_root=REMOTE_ROOT):
    #
    remove_dest_dir(remote_root)
    sudo("mkdir -p {0}".format(remote_root))
    deploy_static(local_root, remote_root)
    deploy_app(local_root, remote_root)

    venv_deploy(remote_root)
    chown_dir(remote_root, user="robbie")
    venv_install_requirements(remote_root)
    chown_dir(remote_root)


