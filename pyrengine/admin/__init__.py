from flask import Blueprint

# this blueprint handles main blog functions: list posts, view post, edit post (for admin only),
# delete post (for admin only), etc
bp = Blueprint('admin', __name__)

from pyrengine.admin import routes

