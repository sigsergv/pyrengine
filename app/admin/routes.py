from flask import render_template
from app.admin import bp

@bp.route('/')
def index():
	return 'ADMIN AREA'

@bp.route('/files')
def files():
	return 'FILES MANAGEMENT'