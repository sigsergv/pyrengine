import re
import uuid

from flask import (render_template, make_response, request, redirect, url_for, abort)
from app.blog import bp
from app.utils import (check_hashed_password, timestamp_to_str, str_to_timestamp, markup, user_has_permission, article_url)
from app.models import (User, Article, Comment, Tag)
from app.models.config import get as get_config
from app.models.article import get_public_tags_cloud
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
    if user.is_anonymous():
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

    return render_template('blog/index.jinja2', **ctx)


@bp.route('/tag/<tag>')
def articles_by_tag(tag):
    return ''


@bp.route('/markup-help')
def markup_help():
    return render_template('blog/markup-help.jinja2')


@bp.route('/<path:shortcut_date>/<shortcut>')
def view_article(shortcut_date, shortcut):
    dbsession = db.session
    q = dbsession.query(Article).filter(Article.shortcut_date == shortcut_date)\
        .filter(Article.shortcut == shortcut)
    article = q.first()

    if article is None:
        abort(404)

    return _view_article(article)

def _view_article(article):
    user = current_user
    if not user_has_permission(user, 'editor') and article.is_draft:
        abort(404)

    dbsession = db.session
    comments = dbsession.query(Comment).filter(Comment.article == article).all()
    comments_dict = {}

    for x in comments:
        if x.parent_id not in comments_dict:
            comments_dict[x.parent_id] = []
        if x.user is not None:
            x._real_email = x.user.email
        else:
            x._real_email = x.email
        if x._real_email == '':
            x._real_email = None
        comments_dict[x.parent_id].append(x)

    scope = {'thread': []}

    # we should hide all not approved comments for everyone who isn't a site admin
    display_not_approved = user_has_permission(user, 'admin')

    def build_thread(parent_id, indent):
        if parent_id not in comments_dict:
            return

        for x in comments_dict[parent_id]:
            if not display_not_approved and not x.is_approved:
                continue
            setattr(x, '_indent', indent)
            scope['thread'].append(x)
            build_thread(x.id, indent+1)

    build_thread(None, 0)
    ctx = {
        'article': article
    }
    ctx['comments'] = scope['thread']

    signature = str(uuid.uuid4()).replace('-', '')
    is_subscribed = False

    for cn in ('comment_display_name', 'comment_email', 'comment_website'):
        if cn in request.cookies:
            ctx[cn] = request.cookies[cn]
        else:
            ctx[cn] = ''

    if 'is_subscribed' in request.cookies and request.cookies['is_subscribed'] == 'true':
        is_subscribed = True

    ctx['article'] = article
    ctx['signature'] = signature
    ctx['is_subscribed'] = is_subscribed

    return render_template('blog/view_article.jinja2', **ctx)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('account/login.jinja2')
    else:
        form = request.form
        login = request.form.get('login')
        password = request.form.get('password')
        dbsession = db.session
        u = dbsession.query(User).filter(User.login == login).first()

        if u is not None:
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
            return render_template('account/login.jinja2', **ctx)
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
            'body': '',
            'is_draft': True,
            'is_commentable': True
        }
        return render_template('blog/edit_article.jinja2', **ctx)
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
        tags = set([s.strip() for s in tags_str.split(',') if s != ''])

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

            get_public_tags_cloud(force_reload=True)

            return redirect(article_url(article))
        else:
            return render_template('blog/edit_article.jinja2', **ctx)


def _update_article(article, ctx):
    ctx['form'] = {x:request.form.get(x) for x in ('title', 'shortcut', 'published', 'tags', 'body') }
    ctx['form']['is_draft'] = request.form.get('is_draft') is not None
    ctx['form']['is_commentable'] = request.form.get('is_commentable') is not None

    errors = _verify_article_form(ctx['form'])
    error_fields = set([f for f,e in errors])

    for field_name in ('title', 'shortcut', 'is_draft', 'is_commentable'):
        setattr(article, field_name, ctx['form'][field_name])

    if 'published' not in error_fields:
        article.published = str_to_timestamp(ctx['form']['published'])
        date_re = re.compile('^([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2})$')
        mo = date_re.match(ctx['form']['published'])
        v = [int(x) for x in mo.groups()[0:3]]
        article.shortcut_date = '{0:04d}/{1:02d}/{2:02d}'.format(*v)
        
    article.set_body(ctx['form']['body'])
    
    dbsession = db.session
    q = dbsession.query(Article).filter(Article.shortcut_date == article.shortcut_date)\
        .filter(Article.shortcut == article.shortcut)\
        .filter(Article.id != article.id)
    res = q.first()
    if res is not None:
        errors.append(('shortcut', _('Article with the same shortcut already exists.')))

    tags_str = ctx['form']['tags']
    tags = set([s.strip() for s in tags_str.split(',') if s != ''])

    for field_name, e in errors:
        if field_name not in ctx['errors']:
            ctx['errors'][field_name] = ''
        ctx['errors'][field_name] += e + ' '

    return errors, tags


@bp.route('/article/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    dbsession = db.session
    article = dbsession.query(Article).get(article_id)
    if article is None:
        abort(404)
    ctx = {
        'article_id': article.id,
        'submit_url': url_for('blog.edit_article', article_id=article_id),
        'mode': 'edit',
        'errors': {}
    }
    if request.method == 'GET':
        article = dbsession.query(Article).get(article_id)
        ctx['form'] = {
            'title': article.title,
            'shortcut': article.shortcut,
            'published': timestamp_to_str(article.published),
            'tags': ', '.join(t.tag for t in article.tags),
            'body': article.body,
            'is_draft': article.is_draft,
            'is_commentable': article.is_commentable
        }
        return render_template('blog/edit_article.jinja2', **ctx)
    else:
        errors, tags = _update_article(article, ctx)

        if len(errors) == 0:
            for tag in article.tags:
                dbsession.delete(tag)
            dbsession.add(article)
            dbsession.flush()
            for tag_str in tags:
                tag = Tag(tag_str, article)
                dbsession.add(tag)
            dbsession.commit()

            get_public_tags_cloud(force_reload=True)

            return redirect(article_url(article))
        else:
            return render_template('blog/edit_article.jinja2', **ctx)


@bp.route('/article/<int:article_id>/edit/ajax', methods=['POST'])
@login_required
def edit_article_ajax(article_id):
    dbsession = db.session
    article = dbsession.query(Article).get(article_id)
    if article is None:
        abort(404)
    jctx = {
        'success': True
    }
    ctx = {
        'errors': {}
    }
    errors, tags = _update_article(article, ctx)
    jctx['errors'] = errors

    if len(errors) == 0:
        for tag in article.tags:
            dbsession.delete(tag)
        dbsession.add(article)
        dbsession.flush()
        for tag_str in tags:
            tag = Tag(tag_str, article)
            dbsession.add(tag)
        dbsession.commit()

        # TODO: force update of tags cloud
    else:
        jctx['success'] = False
    return jctx

@bp.route('/article/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article_ajax(article_id):
    return 'DELETE'


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


@bp.route('/comment/<comment_id>/edit/ajax')
def edit_comment_ajax(comment_id):
    return {}


@bp.route('/article/<int:article_id>/comment/add')
def add_article_comment(article_id):
    return ''