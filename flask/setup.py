from distutils.core import setup

setup(
    name='nwsdb',
    version='0.1.1',
    author='Robert Habermann',
    author_email='mail@rhab.de',
    packages=['nwscandb', 'nwscandb.test'],
    url='',
    license='LICENSE.txt',
    description='A database with small web interface to run and collect nmap scans',
    long_description=open('README.md').read(),
)
