# Initialize development environment

## Environment setup

Base OS: Linux/Debian 12 Bookworm or macos with Homebrew

Install required packages for linux:

~~~~
$ sudo apt install python3 python3-dev postgresql-15 libpq-dev
~~~~

For macos you need standard development tools (compilers etc, install using command `xcode-select --install`). You also

Embedded python3 is too old and you need 3.10 or later, so install python3 package from homebrew:

~~~~
brew install python@3.11
~~~~

Install venv:

~~~~
$ python3.11 -m venv .venv
$ source .venv/bin/activate
(.venv) $
~~~~

Prefix `(.venv)` in shell prompt means that this command must be executed in activated
environment. 

Special step for Macos: you need to specify path to directory with `pg_config` executable,
so if you are using Postgres.app do this:

~~~~
(.venv) $ PATH=/Applications/Postgres.app/Contents/Versions/15/bin/:$PATH pip install psycopg2==2.9.10
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

In macos Postgres.app:

~~~~
$ /Applications/Postgres.app/Contents/Versions/15/bin/createdb pyrengine
$ /Applications/Postgres.app/Contents/Versions/15/bin/createuser pyrengine_user -P
$ /Applications/Postgres.app/Contents/Versions/15/bin/psql pyrengine postgres
psql (15.3)
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
$ /Applications/Postgres.app/Contents/Versions/15/bin/psql -h 127.0.0.1 pyrengine pyrengine_user
~~~~

# Development runtime

## Initialize application database

Use this commands to initialize database and populate with sample data:

~~~~
(.venv) $ export FLASK_APP=pyrengine
(.venv) $ export FLASK_ENV=development
(.venv) $ flask db upgrade
(.venv) $ flask init-db
~~~~

## Create storage directories

~~~~
(.venv) $ mkdir -p storage
~~~~


## Start application in development mode

First copy sample configuration file into the project directory:

~~~~
(.venv) $ cp pyrengine/examples/development.cfg ./
~~~~

Start project:

~~~~
(.venv) $ export FLASK_APP=pyrengine
(.venv) $ export FLASK_ENV=development
(.venv) $ export PYRENGINE_SETTINGS=`pwd`/development.cfg
(.venv) $ export FLASK_DEBUG=1
(.venv) $ flask run
~~~~

Or via Makefile (environment is initialized inside Makefile):

~~~~
(.venv) $ make run
~~~~

Start Flask shell:

~~~~
(.venv) $ export FLASK_APP=pyrengine
(.venv) $ export FLASK_ENV=development
(.venv) $ flask shell
~~~~

Or via Makefile (environment is initialized inside Makefile):

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
(.venv) $ flask shell
Python 3.11.3 (main, Apr  7 2023, 20:13:31) [Clang 14.0.0 (clang-1400.0.29.202)] on darwin
App: app
Instance: /Users/serge/projects/pyrengine/instance
>>> from pyrengine.extensions import db
>>> db.drop_all()
~~~~

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