# Initialize development environment

## Environment setup

Base OS: Debian 12 Bookworm.

Install required packages:

~~~~
$ sudo apt install python3 python3-dev postgresql-15
~~~~

Install venv:

~~~~
$ python3 -m venv .venv
$ source .venv/bin/activate
~~~~

Install required packages:

~~~~
...
~~~~

## Database setup

Configure database:

~~~~
$ sudo -u postgres createdb pyrengine
$ sudo -u postgres createuser pyrengine_user -P
~~~~

Enter and remember password, e.g. `pyreng_pass`.

Test connection (enter password `pyreng_pass`):

~~~~
$ psql -h 127.0.0.1 pyrengine pyrengine_user
~~~~


## Start application in development mode

~~~~
$ export FLASK_APP=app
$ export FLASK_ENV=development
$ export PYRENGINE_SETTINGS=`pwd`/examples/development.cfg
$ flask run
~~~~