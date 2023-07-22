import click

from flask import Flask
from flask_migrate import Migrate
from flask_babel import Babel
from flask.cli import with_appcontext

from app.extensions import db
from app import models

def create_app():
    app = Flask(__name__)
    #app.config.from_object(config_class)
    app.config.from_envvar('PYRENGINE_SETTINGS')

    app.cli.add_command(init_db_command)

    # Initialize Flask extensions here
    db.init_app(app)
    migrate = Migrate(app, db)
    babel = Babel(app)

    # Register blueprints here
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    return app

@click.command('init-db')
@with_appcontext
def init_db_command():
    """[pyrengine] Populate database with default values."""
    db.session.add(models.Config(id='site_copyright', value='Copyright © 2023 SITE OWNER'))
    db.session.add(models.Config(id='site_title', value='YOUR BLOG'))

    db.session.commit()
    click.echo('Initialized the database.')