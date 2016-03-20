from fabric.api import *

# Hosts to deploy onto
env.hosts = ['localhost']

# Where your project code lives on the server
env.project_root = '/home/robbie/work/nmap_tool/nwsdb'

# Where the static files get collected locally. Your STATIC_ROOT setting.
env.local_static_root = '/home/robbie/work/nmap_tool/nwsdb/static_for_prod'

# Where the static files should go remotely
env.remote_static_root = '/var/www/nwsdb/static'

def deploy_static():
    with cd(env.project_root):
        run('/home/robbie/work/nmap_tool/venv/bin/python manage.py collectstatic -v0 --noinput')
        sudo('rm -rf {0}'.format(env.remote_static_root))
        sudo('cp -a {0} {1}'.format(env.local_static_root, env.remote_static_root))
        sudo('chown www-data:www-data {0}'.format(env.remote_static_root))
