from flask import (render_template, make_response, request, redirect, url_for)
from app.main import bp
from app.utils import check_hashed_password
from app.models import User
from app.extensions import db
from app import jinja_helpers
from flask_babel import gettext as _
from flask_login import (login_user, logout_user, login_required, current_user)

@bp.route('/')
def index():
    ctx = {
        'h': jinja_helpers,
        'title': _('Recent articles')
    }
    return render_template('posts/index.html', **ctx)


@bp.route('/write')
def write_article():
    return 'WRITE NEW ARTICLE'


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        ctx = {
            'h': jinja_helpers,
            'title': _('Recent articles')
        }
        return render_template('account/login.html', **ctx)
    else:
        form = request.form
        login = request.form.get('login')
        password = request.form.get('password')
        dbsession = db.session
        u = dbsession.query(User).filter(User.login == login).first()

        if u is not None:
            print(u.password, password)
            if not check_hashed_password(password, u.password):
                u = None
            else:
                # authenticate
                login_user(u, remember=True)
        
        if u is None:
            ctx = {
                'h': jinja_helpers,
                'title': _('Recent articles'),
                'error': _('User not found'),
                'login': login
            }
            return render_template('account/login.html', **ctx)
        else:
            return redirect(url_for('main.index'))


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return {'success': True}


@bp.route('/js/translations')
def js_translations():
    resp = make_response(render_template('js_translations.html'))
    resp.headers['Content-type'] = 'text/javascript; charset=utf-8'
    return resp

