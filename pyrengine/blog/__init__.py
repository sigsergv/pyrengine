from flask import Blueprint

# this blueprint handles main blog functions: list posts, view post, edit post (for admin only),
# delete post (for admin only), etc
bp = Blueprint('blog', __name__)

from pyrengine.blog import routes

