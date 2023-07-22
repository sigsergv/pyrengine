from flask import render_template
from app.main import bp
from app import jinja_helpers
from flask_babel import gettext as _

@bp.route('/')
def index():
    ctx = dict(
        h = jinja_helpers,
        title = _('Recent articles')
    )
    return render_template('posts/index.html', **ctx)

@bp.route('/add')
def add():
    return 'ADD'

