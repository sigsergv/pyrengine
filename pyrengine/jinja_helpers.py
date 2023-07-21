"""
Various helper functions for jinja templates
"""

from sqlalchemy import func

from pyrengine.models.config import Config
from pyrengine.models.config import get as get_config
from pyrengine.models.article import (get_public_tags_cloud, Comment)
from pyrengine.utils import (timestamp_to_str, user_has_permission, article_url, cache)
from pyrengine.extensions import db

def user_link(user):
    name = user.display_name or user.login
    return f'<span class="name"><span class="user-link fa fa-user"></span> {name}</span>'


def get_not_approved_comments_count():
    dbsession = db.session
    cnt = dbsession.query(func.count(Comment.id)).filter(Comment.is_approved==False).scalar()
    return cnt


def get_pages_widget_links(force_reload=False):
    value = cache.get_value('pages_links')
    if value is None or force_reload:
        pages_links = list()
        # fetch from settings, parse, fill cache
        raw = get_config('widget_pages_pages_spec')
        if raw is None:
            raw = ''
        for line in raw.split('\n'):
            line = line.strip()
            if len(line) == 0:
                continue
            # take first char - it's a delimiter
            delim = line[0]
            components = line[1:].split(delim)
            if len(components) != 2:
                continue
            url, title = components
            if not url.startswith('http://') and not url.startswith('https://'):
                continue
            link = {'url': url, 'title': title}
            pages_links.append(link)
    
        value = pages_links
        cache.set_value('pages_links', value)
    
    return value
