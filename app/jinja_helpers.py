"""
Various helper functions for jinja templates
"""

from app.models.config import Config
from app.models.config import get as get_config
from app.models.article import get_public_tags_cloud
from app.utils import (timestamp_to_str, user_has_permission, article_url)


def user_link(user):
    name = user.display_name or user.login
    return f'<span class="name"><span class="user-link fa fa-user"></span> {name}</span>'