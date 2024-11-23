import click
import logging
import os

from flask import (Flask, g, render_template)
from flask_migrate import Migrate
from flask_babel import Babel, gettext as _
from flask.cli import with_appcontext
from flask_login import LoginManager

from pyrengine.extensions import db
from pyrengine.utils import hash_password
from pyrengine import (models, jinja_helpers, notifications, backups, files)

STORAGE_PATH = None
__version__ = '1.0.8'

login_manager = LoginManager()

# if os.getenv('FLASK_DEBUG') == '1':
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    app.config.from_envvar('PYRENGINE_SETTINGS')

    app.cli.add_command(init_db_command)

    init_storage(app)

    # Initialize Flask extensions here
    db.init_app(app)
    migrate = Migrate(app, db)
    babel = Babel(app, locale_selector=get_locale)
    app.jinja_env.globals['get_locale'] = get_locale
    app.jinja_env.globals['h'] = jinja_helpers
    login_manager.init_app(app)
    notifications.init_app(app)

    # Register blueprints here
    from pyrengine.blog import bp as main_bp
    from pyrengine.admin import bp as admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.errorhandler(404)
    def error_404(e):
        ctx = {
            'title': _('Page not found')
        }
        html = render_template('/generic_error.jinja2', **ctx)
        return html, 404

    @app.errorhandler(401)
    def error_401(e):
        ctx = {
            'title': _('Page not found')
        }
        html = render_template('/generic_error.jinja2', **ctx)
        return html, 401

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
    db.session.add(models.Config(id='elements_on_page', value='10'))
    db.session.add(models.Config(id='timezone', value='Asia/Novosibirsk'))
    db.session.add(models.Config(id='site_base_url', value='http://127.0.0.1:5000'))
    db.session.add(models.Config(id='admin_notifications_email', value='test@example.org'))
    db.session.add(models.Config(id='site_search_widget_code', value=''))
    db.session.add(models.Config(id='notifications_from_email', value='no-reply@example.com'))
    db.session.add(models.Config(id='admin_notify_new_comments', value='false'))
    db.session.add(models.Config(id='admin_notify_new_user', value='false'))
    # db.session.add(models.Config(id='comment_answer_msg_subject_tpl', value='{comment_author_name} is answered on subscribed message on site {site_title}'))
    # db.session.add(models.Config(id='comment_answer_msg_body_tpl', value='On {comment_date} visitor {comment_author_name}  is answered on your comment on the article “{article_link}”:\n\n================\n{comment_text}\n================\n\nDirect link to comment: {comment_link}'))
    db.session.add(models.Config(id='admin_notify_new_comment_subject_tpl', value='New comment to the article “{article_title}” {comment_author_name} {comment_author_email} — {site_title}'))
    db.session.add(models.Config(id='admin_notify_new_comment_body_tpl', value='On {comment_date} visitor {comment_author_name} (email: {comment_author_email}) left comment on the article\n“{article_link}”:\n\n================\n{comment_text}\n================\n\nDirect link to comment: {comment_link}'))
    db.session.add(models.Config(id='image_preview_width', value='300'))
    db.session.add(models.Config(id='google_analytics_id', value=''))
    db.session.add(models.Config(id='ui_lang', value='ru'))
    db.session.add(models.Config(id='ui_theme', value='default'))
    db.session.add(models.User(login='admin', password=hash_password('setup'), display_name='Administrator',
        email='admin@example.org', kind='local'))

    db.session.commit()
    click.echo('Initialized the database.')


def get_locale():
    ui_lang = models.config.get('ui_lang')
    return ui_lang


def init_storage(app):
    global STORAGE_PATH

    storage_dir = app.config.get('PYRENGINE_STORAGE_PATH')
    app.config['PYRENGINE_STORAGE_PATH'] = os.path.realpath(storage_dir)
    backups.init(app)
    files.init(app)

