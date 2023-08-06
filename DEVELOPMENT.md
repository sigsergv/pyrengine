# Initialize development environment

## Environment setup

Base OS: Debian 12 Bookworm.

Install required packages:

~~~~
$ sudo apt install python3 python3-dev postgresql-15 libpq-dev
~~~~

Install venv:

~~~~
$ python3 -m venv .venv
$ source .venv/bin/activate
(.venv) $
~~~~

Prefix `(.venv)` in shell prompt means that this command must be executed in activated
environment. 

Install required python packages:

~~~~
(.venv) $ pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-Babel Flask-Login pytz markdown Pygments humanize lxml
~~~~

Install postgres driver, for linux:

~~~~
(.venv) $ pip install psycopg2
~~~~

For macos you need to specify path to directory with `pg_config` executable,
so if you have Postgres.app do this:

~~~~
(.venv) $ PATH=/Applications/Postgres.app/Contents/Versions/15/bin/:$PATH pip install psycopg2
~~~~

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

In macos Posgtres.app:

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


## Initialize application database

Use this commands to initialize database and populate with sample data:

~~~~
(.venv) $ flask db upgrade
(.venv) $ flask init-db
~~~~


# Development runtime

## Start application in development mode

Start project:

~~~~
(.venv) $ export FLASK_APP=app
(.venv) $ export FLASK_ENV=development
(.venv) $ export PYRENGINE_SETTINGS=`pwd`/examples/development.cfg
(.venv) $ export FLASK_DEBUG=1
(.venv) $ flask run
~~~~

Or via Makefile (no need to initialize environment variables):

~~~~
(.venv) $ make run
~~~~

Start Flask shell:

~~~~
(.venv) $ export FLASK_APP=app
(.venv) $ export FLASK_ENV=development
(.venv) $ flask shell
~~~~

Or via Makefile (no need to initialize environment variables):

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
>>> from app.extensions import db
>>> db.drop_all()
~~~~


# Links

* <https://www.digitalocean.com/community/tutorials/how-to-use-templates-in-a-flask-application>
* <https://www.digitalocean.com/community/tutorials/how-to-structure-a-large-flask-application-with-flask-blueprints-and-flask-sqlalchemy>