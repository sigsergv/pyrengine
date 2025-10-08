# Initialize development environment

## Environment setup

Base OS: Linux/Debian 13 Trixie or macos with Miniconda313

Install required packages for linux:

~~~~
$ sudo apt install python3 python3-dev postgresql-17 libpq-dev
~~~~

For Macos you need standard development tools (compilers etc, install using command `xcode-select --install`).

Embedded python3 is too unpredicatable so install miniconda instead, download [package](https://repo.anaconda.com/miniconda/Miniconda3-py313_25.7.0-2-MacOSX-arm64.sh)
from anaconda repository and install to location `~/miniconda313`:

~~~~
./Miniconda3-py313_25.7.0-2-MacOSX-arm64.sh -p ~/miniconda313 -m
~~~~

Install virtual environment. For linux:

~~~~
$ python3.13 -m venv .venv
$ source .venv/bin/activate
(.venv) $
~~~~

For Macos:

~~~~
$ ~/miniconda313/bin/python -m venv .venv
$ source .venv/bin/activate
(.venv) $
~~~~

Prefix `(.venv)` in shell prompt means that this command must be executed in activated
environment. 

Special step for Macos before next step: you need to specify path to directory with `pg_config` executable,
so if you are using Postgres.app do this:

~~~~
(.venv) $ PATH=/Applications/Postgres.app/Contents/Versions/17/bin/:$PATH pip install psycopg2==2.9.10
~~~~

Install application in development mode:

~~~~
(.venv) $ pip install -e .
~~~~

This command will install all required python packages automatically.


## Database setup

Configure database in linux:

~~~~
$ sudo -u postgres createdb pyrengine
$ sudo -u postgres createuser pyrengine_user -P
$ sudo -u postgres psql pyrengine postgres
psql (15.3 (Debian 15.3-0+deb12u1))
Type "help" for help.

pyrengine=# GRANT USAGE, CREATE ON SCHEMA public TO pyrengine_user;
~~~~

In macos Postgres.app (download and install version 17 from their [github repository](https://github.com/PostgresApp/PostgresApp/releases)):

~~~~
$ /Applications/Postgres.app/Contents/Versions/17/bin/createdb pyrengine
$ /Applications/Postgres.app/Contents/Versions/17/bin/createuser pyrengine_user -P
$ /Applications/Postgres.app/Contents/Versions/17/bin/psql pyrengine postgres
psql (17.6 (Postgres.app))
Type "help" for help.

pyrengine=# GRANT USAGE, CREATE ON SCHEMA public TO pyrengine_user;
~~~~

Enter and remember password, e.g. `pyreng_pass`.

Test connection (enter password `pyreng_pass`):

~~~~
$ psql -h 127.0.0.1 pyrengine pyrengine_user
~~~~

Using macos Posgtres.app:

~~~~
$ /Applications/Postgres.app/Contents/Versions/17/bin/psql -h 127.0.0.1 pyrengine pyrengine_user
~~~~


# Development runtime

## Configuration file

First copy sample configuration file into the project directory:

~~~~
(.venv) $ cp pyrengine/examples/development.cfg ./
~~~~

## Initialize application database

Use this commands to initialize database and populate with sample data:

~~~~
(.venv) $ make init-db
~~~~

## Create storage directories

~~~~
(.venv) $ mkdir -p storage
~~~~


## Start application in development mode

Start project:

~~~~
(.venv) $ make run
~~~~

Or with custom host:

~~~~
(.venv) $ make FLASK_HOST=192.168.88.29 run
~~~~

Start Flask shell:

~~~~
(.venv) $ make flask-shell
~~~~

## Translation and internationalization

See detailed help at <https://python-babel.github.io/flask-babel/>.

Extract translations from all supported files and update .po-files:

~~~~
(.venv) $ make babel-collect
~~~~

Compile translations:

~~~~
(.venv) $ make babel-compile
~~~~

## Reset and database cleanup

To quickly drop all databases use this command in `psql` console:

~~~~
DO $$ DECLARE
    r RECORD;
BEGIN
    -- if the schema you operate on is not "current", you will want to
    -- replace current_schema() in query with 'schematodeletetablesfrom'
    -- *and* update the generate 'DROP...' accordingly.
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
~~~~

# Working with SQLAlchemy

## Initialize migrations

This task should be performed during early stages of development only. When database schema is finished
commit the directory `migrations`.

~~~~
(.venv) $ rm -rf migrations
(.venv) $ flask db init
(.venv) $ flask db migrate -m "Initial migration."
~~~~

## Using Flask-Migrate

We are using Alembic to propagate all database changes including initial database
creation. 

See also <https://flask-migrate.readthedocs.io/en/latest/index.html>.

To create initial database on application init:

~~~~
(.venv) $ flask db upgrade
(.venv) $ flask init-db
~~~~

## Using flask shell to drop all database tables

To drop all created tables use this commands:

~~~~
(.venv) $ make flask-shell
Python 3.13.5 | packaged by Anaconda, Inc. | (main, Jun 12 2025, 11:23:37) [Clang 14.0.6 ] on darwin
App: pyrengine
Instance: /Users/serge/projects/pyrengine/instance
>>> from pyrengine.extensions import db
>>> db.drop_all()
~~~~

You also need to drop table `alembic_version` from psql shell:

~~~
pyrengine=> drop table alembic_version;
DROP TABLE
~~~


# Deployment

We deploy application using wheel. First install package `build` required for package creation:

~~~~
(.venv) $ pip install build setuptools
~~~~

Create distribution package:

~~~~
(.venv) $ make build
~~~~

Resulting wheel package will be placed to directory `dist/`, it looks like `pyrengine-1.0.0-py3-none-any.whl`.



# Links

* <https://www.digitalocean.com/community/tutorials/how-to-use-templates-in-a-flask-application>
* <https://www.digitalocean.com/community/tutorials/how-to-structure-a-large-flask-application-with-flask-blueprints-and-flask-sqlalchemy>