import click

from flask import Flask
from flask_migrate import Migrate
from flask_babel import Babel
from flask.cli import with_appcontext
from flask_login import LoginManager

from app.extensions import db
from app.utils import hash_password
from app import models

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    #app.config.from_object(config_class)
    app.config.from_envvar('PYRENGINE_SETTINGS')

    app.cli.add_command(init_db_command)

    # Initialize Flask extensions here
    db.init_app(app)
    migrate = Migrate(app, db)
    babel = Babel(app)
    login_manager.init_app(app)

    # Register blueprints here
    from app.main import bp as main_bp
    from app.admin import bp as admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    return app


@login_manager.user_loader
def user_loader(user_id):
    dbsession = db.session
    return dbsession.query(models.User).filter(models.User.login == user_id).first()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """[pyrengine] Populate database with default values."""
    # command will fail if database is already populated.
    db.session.add(models.Config(id='site_copyright', value='Copyright © 2023 SITE OWNER'))
    db.session.add(models.Config(id='site_title', value='YOUR BLOG'))
    db.session.add(models.User(login='admin', password=hash_password('setup'), display_name='Administrator',
        email='admin@example.org', kind='local'))

    db.session.commit()
    click.echo('Initialized the database.')

