import re
import uuid
import os

from flask import (render_template, make_response, request, redirect, url_for, abort)
from app.blog import bp
from app import notifications
from app.utils import (check_hashed_password, timestamp_to_str, str_to_timestamp, timestamp_to_dt, markup, user_has_permission, article_url, normalize_email)
from app.utils.PyRSS2Gen import RSS2, RSSItem
from app.models import (User, Article, Comment, Tag, VerifiedEmail, File)
from app.models.config import get as get_config
from app.models.article import get_public_tags_cloud
from app.extensions import db
from sqlalchemy import func
from app.files import FILES_PATH

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
    # print(current_user)
    if user.is_anonymous:
        q = q.filter(Article.is_draft==False)

    ctx['articles'] = q[(start_page * page_size):(start_page+1) * page_size + 1]

    #for article in ctx['articles']:
    #    log.debug(article.shortcut_date)

    if len(ctx['articles']) > page_size:
        ctx['prev_page'] = url_for('blog.index', start=start_page+1)
        ctx['articles'].pop()

    ctx['next_page'] = None
    if start_page > 0:
        ctx['next_page'] = url_for('blog.indx', start=start_page+1)

    ctx['page_title'] = _('Latest articles')

    return render_template('blog/index.jinja2', **ctx)


@bp.route('/files/f/<filename>')
def download_file(filename):
    dbsession = db.session

    dbfile = dbsession.query(File).filter(File.name==filename).first()
    if dbfile is None:
        abort(404)

    full_filename = os.path.join(FILES_PATH, filename)
    data = open(full_filename, 'rb').read()
    resp = make_response(data)
    resp.mimetype = dbfile.content_type
    return resp


@bp.route('/rss/latest')
def latest_rss():
    dbsession = db.session

    q = dbsession.query(Article).options(db.joinedload(Article.tags))\
        .options(db.joinedload(Article.user))\
        .filter(Article.is_draft==False).order_by(Article.updated.desc())
    articles = q[0:10]
    rss_title = get_config('site_title') + ' - ' + _('Latest articles feed')
    site_base_url = get_config('site_base_url')
    items = []

    '''
    feed = Rss201rev2Feed(
        title=rss_title,
        link=site_base_url,
        description='',
        language='en')
    '''

    for a in articles:
        link = article_url(a)
        tags_list = []
        for t in a.tags:
            tags_list.append(t.tag)
        items.append(RSSItem(title=a.title, link=link, description=a.rendered_preview, pubDate=timestamp_to_dt(a.published),
            guid=str(a.id)))

    feed = RSS2(
        title=rss_title,
        link=site_base_url,
        description='',
        items=items,
        generator='pyrengine'
        )

    # response = Response(body=feed.to_xml(encoding='utf-8'), content_type='application/rss+xml')
    resp = make_response(feed.to_xml(encoding='utf-8'), )
    return resp


@bp.route('/tag/<tag>')
def articles_by_tag(tag):
    return ''


@bp.route('/help/article-markup')
def article_markup_help():
    return render_template('blog/markup_help.jinja2')


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
    # ctx['comments_html'] = 'COMMENTS'

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
        # 'save_url_ajax': url_for('blog.write_article_ajax'),
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



@bp.route('/article/<int:article_id>/comment/add', methods=['POST'])
def add_article_comment(article_id):
    """
    Honeypot
    """
    return ''


@bp.route('/article/<int:article_id>/comment/add/ajax', methods=['POST'])
def add_article_comment_ajax(article_id):
    dbsession = db.session

    q = dbsession.query(Article).filter(Article.id == article_id)
    user = current_user
    if not user_has_permission(user, 'editor') or not user_has_permission(user, 'admin'):
        q = q.filter(Article.is_draft==False)
    article = q.first()

    if article is None or not article.is_commentable:
        return abort(404)

    if 's' not in request.form:
        return abort(400)

    json = {}

    key = request.form['s']

    # all data elements are constructed from the string "key" as substrings
    body_ind = key[3:14]
    parent_ind = key[4:12]
    display_name_ind = key[0:5]
    email_ind = key[13:25]
    website_ind = key[15:21]
    is_subscribed_ind = key[19:27]

    for ind in (body_ind, parent_ind, display_name_ind, email_ind, website_ind):
        if ind not in request.form:
            return HTTPBadRequest()

    body = request.form[body_ind]

    if len(body) == 0:
        return {
            'success': False,
            'error': _('Empty comment body is not allowed.')
        }

    comment = Comment()
    comment.set_body(body)

    cookies = []

    if not user.is_anonymous:
        comment.user_id = user.id
    else:
        # get "email", "display_name" and "website" arguments
        comment.display_name = request.form[display_name_ind]
        comment.email = request.form[email_ind]
        comment.website = request.form[website_ind]

        # remember email, display_name and website in browser cookies
        cookies.append( ('comment_display_name', comment.display_name, 31536000) )
        cookies.append( ('comment_email', comment.email, 31536000) )
        cookies.append( ('comment_website', comment.website, 31536000) )

    # set parent comment
    parent_id = request.form[parent_ind]
    try:
        parent_id = int(parent_id)
    except ValueError:
        parent_id = None

    if parent_id:
        parent = dbsession.query(Comment).filter(Comment.id == parent_id)\
            .filter(Comment.article_id == article_id).first()
        if parent is not None:
            if not parent.is_approved:
                #
                data = { 'error': _('Answering to not approved comment')}
                return json.dumps(data)

    comment.parent_id = parent_id
    comment.article_id = article_id

    if is_subscribed_ind in request.form:
        comment.is_subscribed = True

    # this list contains notifications
    ns = []

    # if user has subscribed to answer then check is his/her email verified
    # if doesn't send verification message to the email
    if is_subscribed_ind in request.form:
        vrf_email = ''
        if not user.is_anonymous:
            vrf_email = user.email
        elif request.form[email_ind]:
            vrf_email = request.form[email_ind]

        vrf_email = normalize_email(vrf_email)
        if vrf_email:
            # email looks ok so proceed

            send_evn = False

            vf = dbsession.query(VerifiedEmail).filter(VerifiedEmail.email == vrf_email).first()
            vf_token = ''
            if vf is not None:
                if not vf.is_verified:
                    diff = time() - vf.last_verify_date
                    #if diff > 86400:
                    if diff > 1:
                        # delay between verifications requests must be more than 24 hours
                        send_evn = True
                    vf.last_verify_date = time()
                    vf_token = vf.verification_code

            else:
                send_evn = True
                vf = VerifiedEmail(vrf_email)
                vf_token = vf.verification_code
                dbsession.add(vf)

            if send_evn:
                ns.append(notifications.gen_email_verification_notification(vrf_email, vf_token))

    cookies.append( ('is_subscribed', 'true' if comment.is_subscribed else 'false', 31536000) )
    # request.response.set_cookie('is_subscribed', 'true' if comment.is_subscribed else 'false', max_age=31536000)

    # automatically approve comment if user has role "admin", "writer" or "editor"
    if user_has_permission(user, 'admin') or user_has_permission(user, 'editor'):
        comment.is_approved = True

    # TODO: also automatically approve comment if it's considered as safe:
    # i.e. without hyperlinks, spam etc

    # check how much hyperlinks in the body string
    if len(re.findall('https?://', body, flags=re.IGNORECASE)) <= 1:
        comment.is_approved = True

    # record commenter ip address
    comment.ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
    comment.xff_ip_address = request.environ.get('X_FORWARDED_FOR', None)

    dbsession.add(comment)
    _update_comments_counters(article)
    dbsession.flush()
    dbsession.expunge(comment)  # remove object from the session, object state is preserved
    dbsession.expunge(article)
    dbsession.commit()

    # comment added, now send notifications
    loop_limit = 100
    comment = dbsession.query(Comment).get(comment.id)
    parent = comment.parent
    admin_email = get_config('admin_notifications_email')
    vf_q = dbsession.query(VerifiedEmail)
    notifications_emails = []

    while parent is not None and loop_limit > 0:
        loop_limit -= 1
        c = parent
        parent = c.parent
        # walk up the tree
        if not c.is_subscribed:
            continue
        # find email
        email = None
        if c.user is None:
            email = c.email
        else:
            email = c.user.email

        if email is None or email == admin_email:
            continue

        email = normalize_email(email)

        if email in notifications_emails:
            continue

        vf = vf_q.filter(VerifiedEmail.email == email).first()
        if vf is not None and vf.is_verified:
            # send notification to "email"
            ns.append(notifications.gen_comment_response_notification(request, article, comment, c, email))

    admin_notifications_email = normalize_email(get_config('admin_notifications_email'))

    for nfn in ns:
        if nfn is None:
            continue

        if nfn.to == admin_notifications_email:
            continue
        nfn.send()

    # create special notification for the administrator
    nfn = notifications.gen_new_comment_admin_notification(article, comment)
    if nfn is not None:
        nfn.send()

    # cosntruct comment_id
    comment_url = article_url(article) + '?commentid=' + str(comment.id)

    # return rendered comment
    data = {
        'body': comment.rendered_body,
        'approved': comment.is_approved,
        'id': comment.id,
        'url': comment_url
        }

    resp = make_response(data)
    for cookie_name, cookie_value, cookie_max_age in cookies:
        resp.set_cookie(cookie_name, cookie_value, max_age=cookie_max_age)

    return resp


@bp.route('/article/comment/<int:comment_id>/approve/ajax', methods=['POST'])
@login_required
def approve_comment_ajax(comment_id):
    dbsession = db.session
    comment = dbsession.query(Comment).get(comment_id)
    if comment is None:
        abort(404)

    # also find corresponding article
    article = dbsession.query(Article).get(comment.article_id)

    if article is None:
        abort(404)

    comment.is_approved = True

    _update_comments_counters(article)
    dbsession.commit()

    data = {}
    return data


@bp.route('/article/comment/<int:comment_id>/edit/ajax', methods=['POST'])
@login_required
def edit_comment_ajax(comment_id):
    """
    Update comment and return updated and rendered data
    """
    dbsession = db.session

    comment = dbsession.query(Comment).options(db.joinedload(Comment.user)).get(comment_id)

    # passed POST parameters are: 'body', 'name', 'email', 'website', 'date', 'ip', 'xffip'
    params = {
        'body': 'body', 
        'name': 'display_name',
        'email': 'email',
        'website': 'website',
        'ip': 'ip_address',
        'xffip': 'xff_ip_address'
        }

    for k, v in params.items():
        value = request.form[k]
        if value == '':
            value = None
        setattr(comment, v, value)

    comment.set_body(request.form['body'])
    comment.is_subscribed = 'is_subscribed' in request.form

    comment.published = str_to_timestamp(request.form['date'])
    dbsession.flush()

    #comment_user = None
    #if comment.user is not None:
    #    comment_user = dbsession.query(User).options(joinedload('roles')).get(comment.user)

    dbsession.expunge(comment)
    if comment.user is not None:
        dbsession.expunge(comment.user)

    data = {}

    # without "unicode" or "str" it generates broken HTML
    # because render() returns webhelpers.html.builder.literal
    renderer_dict = {'comment': comment}
    if comment.user is not None:
        comment._real_email = comment.user.email
    else:
        comment._real_email = comment.email

    if comment._real_email == '':
        comment._real_email = None

    dbsession.commit()

    data['rendered'] = render_template('/blog/article_comment.jinja2', **renderer_dict)
    return data

@bp.route('/article/comment/<int:comment_id>/fetch/ajax', methods=['POST'])
@login_required
def comment_fetch_ajax(comment_id):
    dbsession = db.session

    comment = dbsession.query(Comment).get(comment_id)

    attrs = ('display_name', 'email', 'website', 'body', 'ip_address', 'xff_ip_address', 'is_subscribed')
    data = {}
    for a in attrs:
        data[a] = getattr(comment, a)

    data['date'] = timestamp_to_str(comment.published)

    return data


@bp.route('/article/comment/<comment_id>/delete/ajax', methods=['POST'])
@login_required
def delete_comment_ajax(comment_id):
    dbsession = db.session
    comment = dbsession.query(Comment).get(comment_id)
    if comment is None:
        return HTTPNotFound()

    dbsession.delete(comment)
    dbsession.commit()
    article = dbsession.query(Article).get(comment.article_id)
    _update_comments_counters(article)

    data = {}
    return data

@bp.route('/comments/moderation', methods=['POST', 'GET'])
def comments_moderation():
    if request.method == 'GET':
        ctx = {
            'comments': []
        }

        dbsession = db.session
        comments = dbsession.query(Comment).filter(Comment.is_approved==False).all()
            
        for x in comments:
            # set real email
            if x.user is not None:
                x._real_email = x.user.email
            else: 
                x._real_email = x.email
            if x._real_email == '':
                x._real_email = None
            
            # truncate comment text
            trunc_pos = 200
            x._truncated_body = None
            if len(x.rendered_body) > trunc_pos:
                x._truncated_body = x.rendered_body[0:trunc_pos]
            
            ctx['comments'].append(x)

        return render_template('blog/comments_moderation.jinja2', **ctx)
    else:
        return ''

def _update_comments_counters(article):
    """
    Re-count total and approved comments and update corresponding counters for the article
    """
    dbsession = db.session
    approved_cnt = dbsession.query(func.count(Comment.id))\
        .filter(Comment.article == article)\
        .filter(Comment.is_approved==True).scalar()
    total_cnt = dbsession.query(func.count(Comment.id)).filter(Comment.article == article).scalar()
    article.comments_approved = approved_cnt
    article.comments_total = total_cnt

