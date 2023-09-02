# Installation

Install required system packages:

~~~~
$ sudo apt install nginx uwsgi uwsgi-plugin-python3 python3 python3-dev python3-venv postgresql-15 gcc libpq-dev
~~~~

Create separate system user for the server runtime, do not start it as root user.

~~~~
$ sudo adduser --disabled-password blog
$ sudo chmod 0755 /home/blog/
~~~~

Create postgres database and user, create and remember user password:

~~~~
$ sudo -u postgres createdb pyrengine
$ sudo -u postgres createuser pyrengine_user -P
$ sudo -u postgres psql pyrengine postgres
psql (15.3 (Debian 15.3-0+deb12u1))
Type "help" for help.

pyrengine=# GRANT USAGE, CREATE ON SCHEMA public TO pyrengine_user;
~~~~

Switch to a new user:

~~~~
$ sudo -u blog -i
~~~~

Create a new application directories (as user `blog`) and initialize virtualenv there:

~~~~
$ mkdir /home/blog/pyrengine-blog
$ mkdir /home/blog/pyrengine-blog/storage
$ python3 -m venv ~blog/pyrengine-blog/venv
$ source ~blog/pyrengine-blog/venv/bin/activate
~~~~

Fetch latest version (.whl-file) from releases page <https://github.com/sigsergv/pyrengine/releases> and install it:

~~~~
(venv) $ pip install pyrengine-1.0.0-py3-none-any.whl
~~~~

Initialize production config:

~~~~
$ cp $(python3 -m pyrengine.utils -s examples_dir)/production.cfg /home/blog/pyrengine-blog/production.cfg
~~~~

Open it in text editor and set new SECRET_KEY, mail server and database connection parameters (only password if you follow this instruction). You can generate SECRET_KEY using this oneliner: 

~~~~
$ python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
~~~~

Initialize database:

~~~~
$ export PYRENGINE_SETTINGS=/home/blog/pyrengine-blog/production.cfg
$ export FLASK_APP=pyrengine
$ source pyrengine-blog/venv/bin/activate
(venv) $ flask db upgrade -d $(python3 -m pyrengine.utils -s alembic_migrations)
(venv) $ flask init-db
~~~~


Now switch back to system user.

Copy nginx configuration file and edit it accordingly:

~~~~
$ sudo cp $(/home/blog/pyrengine-blog/venv/bin/python3 -m pyrengine.utils -s examples_dir)/pyrengine-nginx-uwsgi.conf /etc/nginx/sites-enabled/pyrengine-blog.conf
~~~~

Copy uWSGI configuration file:

~~~~
$ sudo cp $(/home/blog/pyrengine-blog/venv/bin/python3 -m pyrengine.utils -s examples_dir)/pyrengine-uwsgi.ini /etc/uwsgi/apps-enabled/pyrengine-blog.ini
~~~~

uWSGI log file is `/var/log/uwsgi/app/pyrengine-blog.log`.

Restart nginx and uwsgi:

~~~~
$ sudo systemctl restart nginx
$ sudo systemctl restart uwsgi
~~~~




# Upgrade

Fetch latest version from releases page <https://github.com/sigsergv/pyrengine/releases>.

Install package to virtual environment.
