from flask import Blueprint

# this blueprint handles main blog functions: list posts, view post, edit post (for admin only),
# delete post (for admin only), etc
bp = Blueprint('main', __name__)

from app.main import routes

