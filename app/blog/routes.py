import re

from flask import (render_template, make_response, request, redirect, url_for)
from app.blog import bp
from app.utils import (check_hashed_password, timestamp_to_str, str_to_timestamp, markup)
from app.models import (User, Article, Tag)
from app.models.config import get as get_config
from app.extensions import db

from flask_babel import gettext as _
from flask_login import (login_user, logout_user, login_required, current_user)
from time import time

@bp.route('/')
def index():
    """
    Display list of articles sorted by publishing date ascending,
    show rendered previews, not complete articles
    """
    ctx = {
        'articles': [],
        'prev_page': None,
        'next_page': None
    }
    page_size = int(get_config('elements_on_page'))
    start_page = 0
    if 'start' in request.args:
        try:
            start_page = int(request.args['start'])
            if start_page < 0:
                start_page = 0
        except ValueError:
            start_page = 0
    
    dbsession = db.session
    user = current_user

    q = dbsession.query(Article).options(db.joinedload(Article.tags)).options(db.joinedload(Article.user)).order_by(Article.published.desc())
    if user.is_anonymous:
        q = q.filter(Article.is_draft==False)

    ctx['articles'] = q[(start_page * page_size):(start_page+1) * page_size + 1]

    #for article in ctx['articles']:
    #    log.debug(article.shortcut_date)

    if len(ctx['articles']) > page_size:
        ctx['prev_page'] = route_url('blog_latest', request, _query=[('start', start_page+1)])
        ctx['articles'].pop()

    ctx['next_page'] = None
    if start_page > 0:
        ctx['next_page'] = route_url('blog_latest', request, _query=[('start', start_page-1)])

    ctx['page_title'] = _('Latest articles')

    return render_template('blog/index.html', **ctx)


@bp.route('/tag/<tag>')
def articles_by_tag():
    return ''

@bp.route('/markup-help')
def markup_help():
    return render_template('blog/markup-help.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('account/login.html')
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
                'error': _('User not found'),
                'login': login
            }
            return render_template('account/login.html', **ctx)
        else:
            return redirect(url_for('blog.index'))


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return {'success': True}


@bp.route('/write', methods=['GET', 'POST'])
@login_required
def write_article():
    ctx = {
        'submit_url': url_for('blog.write_article'),
        'mode': 'create',
        'save_url_ajax': url_for('blog.save_article_ajax'),
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
        for field_name in ('title', 'shortcut', 'is_draft', 'is_commentable'):
            setattr(article, field_name, ctx['form'][field_name])
        article.published = str_to_timestamp(ctx['form']['published'])
        date_re = re.compile('^([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2})$')
        mo = date_re.match(ctx['form']['published'])
        v = [int(x) for x in mo.groups()[0:3]]
        article.shortcut_date = '{0:04d}/{1:02d}/{2:02d}'.format(*v)
        article.set_body(ctx['form']['body'])
        
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


@bp.route('/article/<article_id>/edit', methods=['POST'])
@login_required
def edit_article(article_id):
    return 'EDIT'


@bp.route('/article/<article_id>/delete', methods=['POST'])
@login_required
def delete_article_ajax(article_id):
    return 'DELETE'


@bp.route('/save-article', methods=['POST'])
@login_required
def save_article_ajax():
    pass


@bp.route('/article/preview', methods=['POST'])
@login_required
def preview_article():
    preview, complete = markup.render_text_markup(request.form['body'])

    return complete



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
