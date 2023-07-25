"""
Various helper functions for jinja templates
"""
from flask import url_for

from app.models.config import Config
# from app.extensions import db
from app.models.config import get as get_config
from app.utils import timestamp_to_str

def user_has_permission(user, p):
    if p == 'editor' and user.is_authenticated():
        return True

    if p == 'admin' and user.is_authenticated():
        return True

    return False

def article_url(article):
    return '{0}{1}/{2}'.format(url_for('blog.index'), article.shortcut_date, article.shortcut)