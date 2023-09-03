"""
Notifications
"""

import logging
import urllib
import re
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from multiprocessing import Process

from pyrengine.utils import (full_article_url, timestamp_to_str, normalize_email)
from flask import render_template
# from pyramid.renderers import render

# from pyrone.models.config import get as get_config
# from pyrone.models.user import normalize_email
# from pyrone.lib.lang import lang
# from pyrone.lib import helpers as h
from pyrengine.models.config import get as get_config

log = logging.getLogger(__name__)

context = {
    'enable_email': False,
    'smtp_server': None,
    'email_transport': None
}

def init_app(app):

    if not app.config.get('PYRENGINE_NOTIFICATION_MAIL'):
        return

    context['email_transport'] = app.config.get('PYRENGINE_NOTIFICATION_MAIL_TRANSPORT')
    if context['email_transport'] not in ('smtp', 'dummy'):
        log.error('Not supported email transport "{0}"'.format(context['email_transport']))
        return

    context['enable_email'] = True
    context['smtp_server'] = app.config.get('PYRENGINE_NOTIFICATION_MAIL_SMTP_SERVER')

COMMASPACE = ', '
SUBJECT_RE = re.compile(r'^Subject: ([^\n\r]+)')

def send_email_process(ctx, html, recipients, sender):
    """Process for real sending emails"""

    # now cut out subject line from the message
    mo = SUBJECT_RE.match(html)
    # print(html)
    if mo is None:
        subject = 'NO-SUBJECT'
    else:
        subject = mo.group(1)
        html = SUBJECT_RE.sub('', html, 1)

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = COMMASPACE.join(recipients)
    msg.preamble = 'Use multipart, Luke'

    html_part = MIMEText(html, 'html', 'utf-8')
    msg.attach(html_part)


    if ctx['email_transport'] == 'dummy':
        log.debug('--------------------------------------------------')
        debug_data = '''
            SEND NOTIFICATION:
            Subject: {subject}
            To: {to}

            {body}
            '''.format(subject=subject, to=msg['To'], body=html)
        log.debug(debug_data)
        log.debug('--------------------------------------------------')
        log.debug(ctx)
    elif ctx['email_transport'] == 'smtp':
        with SMTP(ctx['smtp_server']) as smtp:
            smtp.send_message(msg)


class Notification:
    """
    Object represents notification object
    """
    to = None
    # request = None
    html = ''

    def send(self):

        if not context['enable_email']:
            log.debug('mail sending is not allowed in config')
            return

        sender = get_config('notifications_from_email')
        Process(target=send_email_process, args=(context, self.html, 
            [self.to], sender)).start()

    def __init__(self, html, to):
        self.to = to
        self.html = html


def _extract_comment_sub(comment):
    """
    Extract placeholders substitution strings from the comment object
    """
    author_name = comment.display_name
    author_email = comment.email

    if comment.user is not None:
        author_name = comment.user.display_name
        author_email = comment.user.email

    if author_email == '':
        author_email = '<em>no-email</em>'

    # construct comment link
    article = comment.article
    comment_url = full_article_url(article) + '#comment-' + str(comment.id)

    comment_date = timestamp_to_str(comment.published)
    res = {
        'comment_author_email': author_email,
        'comment_author_name': author_name,
        'comment_text': comment.body,
        'comment_date': comment_date,
        'comment_url': comment_url
        }
    return res


def _extract_article_sub(article):
    """
    Extract placeholders substitution strings from the article object
    """

    res = {
        'article_title': article.title,
        'article_url': full_article_url(article)
        }
    return res


def gen_comment_response_notification(article, comment, top_comment, email):
    """
    Generate comment answer notification
    """

    email = normalize_email(email)
    if not email:
        return None

    # placeholders replacements
    params = {
        'site_title': get_config('site_title')
    }
    params.update(_extract_comment_sub(comment))
    params.update(_extract_article_sub(article))

    html = render_template('/email/comment_response.jinja2', **params)

    n = Notification(html, email)

    return n


def gen_email_verification_notification(email, verification_code):
    """
    Generate email address verification notification.
    """

    email = normalize_email(email)
    if not email:
        return None

    # placeholders replacements
    base_url = get_config('site_base_url')
    q = urllib.parse.urlencode({'token': verification_code, 'email': email})
    verify_url = base_url + '/verify-email?' + q
    params = {
        'site_title': get_config('site_title'),
        'email': email,
        'verify_url': verify_url
    }

    html = render_template('/email/email_verification.jinja2', **params)

    n = Notification(html, email)

    return n


def gen_new_comment_admin_notification(article, comment):
    """
    Generate new comment notification for the administrator.
    """
    email = normalize_email(get_config('admin_notifications_email'))
    if not email:
        return None

    # placeholders replacements
    params = {
        'site_title': get_config('site_title')
    }
    params.update(_extract_comment_sub(comment))
    params.update(_extract_article_sub(comment.article))

    html = render_template('/email/admin_new_comment.jinja2', **params)

    n = Notification(html, email)

    return n
