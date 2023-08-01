"""
Various helper functions for jinja templates
"""

from sqlalchemy import func

from app.models.config import Config
from app.models.config import get as get_config
from app.models.article import (get_public_tags_cloud, Comment)
from app.utils import (timestamp_to_str, user_has_permission, article_url)
from app.extensions import db

def user_link(user):
    name = user.display_name or user.login
    return f'<span class="name"><span class="user-link fa fa-user"></span> {name}</span>'

def get_not_approved_comments_count():
    dbsession = db.session
    cnt = dbsession.query(func.count(Comment.id)).filter(Comment.is_approved==False).scalar()
    return cnt
