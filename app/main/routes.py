import re

from flask import (render_template, make_response, request, redirect, url_for)
from app.main import bp
from app.utils import (check_hashed_password, timestamp_to_str, str_to_timestamp)
from app.models import (User, Article, Tag)
from app.extensions import db
from app import jinja_helpers
from flask_babel import gettext as _
from flask_login import (login_user, logout_user, login_required, current_user)
from time import time

@bp.route('/')
def index():
    ctx = {
        'h': jinja_helpers
    }
    return render_template('blog/index.html', **ctx)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        ctx = {
            'h': jinja_helpers
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


@bp.route('/write', methods=['GET', 'POST'])
@login_required
def write_article():
    ctx = {
        'h': jinja_helpers,
        'title': _('Write new article'),
        'submit_url': url_for('main.write_article'),
        'mode': 'create',
        'save_url_ajax': url_for('main.save_article_ajax'),
        'errors': {}
    }
    if request.method == 'GET':
        ctx['form'] = {
            'title': _('New article title'),
            'shortcut': 'new-article-shortcut',
            'published': timestamp_to_str(time()),  # current time
            'tags': '',
            'body': ''
        }
        return render_template('blog/edit_article.html', **ctx)
    else:
        ctx['form'] = {x:request.form.get(x) for x in ('title', 'shortcut', 'published', 'tags', 'body') }
        ctx['form']['is_draft'] = request.form.get('is_draft') is not None
        ctx['form']['is_commentable'] = request.form.get('is_commentable') is not None

        errors = _verify_article_form(ctx['form'])

        article = Article()
        article.user = current_user
        for field_name in ('title', 'shortcut', 'body', 'is_draft', 'is_commentable'):
            setattr(article, field_name, ctx['form'][field_name])
        article.published = str_to_timestamp(ctx['form']['published'])
        date_re = re.compile('^([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2})$')
        mo = date_re.match(ctx['form']['published'])
        v = [int(x) for x in mo.groups()[0:3]]
        article.shortcut_date = '{0:04d}/{1:02d}/{2:02d}'.format(*v)
        
        dbsession = db.session
        q = dbsession.query(Article).filter(Article.shortcut_date == article.shortcut_date)\
            .filter(Article.shortcut == article.shortcut)
        res = q.first()
        if res is not None:
            errors.append(('shortcut', _('Article with the same shortcut already exists.')))

        tags_str = ctx['form']['tags']
        tags = set([s.strip() for s in tags_str.split(',')])

        for field_name, e in errors:
            if field_name not in ctx['errors']:
                ctx['errors'][field_name] = ''
            ctx['errors'][field_name] += e + ' '

        if len(errors) == 0:
            # create database object
            dbsession.add(article)
            dbsession.flush()  # required as we need to obtain article_id
            for tag_str in tags:
                tag = Tag(tag_str, article)
                dbsession.add(tag)
            dbsession.commit()

            # force update of tags cloud

            # redirect to new article URL
        else:
            return render_template('blog/edit_article.html', **ctx)


@bp.route('/save-article', methods=['POST'])
def save_article_ajax():
    pass


@bp.route('/js/translations')
def js_translations():
    resp = make_response(render_template('js_translations.html'))
    resp.headers['Content-type'] = 'text/javascript; charset=utf-8'
    return resp


def _verify_article_form(form):
    errors = []
    # check required fields
    for f in ('title', 'shortcut', 'body', 'published'):
        if form.get(f, '') == '':
            errors.append( (f, _('Field is required.')) )

    date_re = re.compile('^([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2})$')
    mo = date_re.match(form['published'])
    if mo is None:
        errors.append(('published', _('Invalid date format.')))

    return errors
