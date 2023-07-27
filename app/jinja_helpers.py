"""
Various helper functions for jinja templates
"""

from app.models.config import Config
# from app.extensions import db
from app.models.config import get as get_config
from app.models.article import get_public_tags_cloud
from app.utils import (timestamp_to_str, user_has_permission, article_url)


def form_checkbox(name, title, value, errors, help=None, label=None, label_help=None):
    # ignore errors

    if label is not None and label_help is not None:
        label = '<acronym title="{help}">{title}</acronym>'.format(help=label_help, title=label)

    html = ""

    if title is not None:
        html += """<dt>{title}</dt>""".format(title=title)

    cb = '<input type="checkbox" name="{name}" id="fid-{name}"{checked}/>'.format(name=name,
        checked=' checked="checked"' if value is True else '')
    if label is not None:
        cb = '<label>{cb} {label}</label>'.format(cb=cb, label=label)

    html += '<dd>{cb}</dd>'.format(cb=cb)
    return html


def user_link(user):
    name = user.display_name or user.login
    return f'<span class="name"><span class="user-link fa fa-user"></span> {name}</span>'