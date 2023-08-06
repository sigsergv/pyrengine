from flask import (render_template, abort)
from app.admin import bp
from app import backups
from app.utils import cache

from flask_login import (login_user, logout_user, login_required, current_user)

@bp.route('/')
@login_required
def index():
    return 'ADMIN AREA'

@bp.route('/files')
@login_required
def files():
    return 'FILES MANAGEMENT'


@bp.route('/backups')
@login_required
def backups_list():
    ctx = {
        'backups': backups.list_backups()
    }
    return render_template('admin/backups_list.jinja2', **ctx)


@bp.route('/backups/create', methods=['POST'])
@login_required
def backup_now():
    return {}


@bp.route('/backups/restore/<backup_id>', methods=['POST'])
@login_required
def restore_backup(backup_id):
    res = backups.restore_backup(backup_id)
    if res is True:
        # clear cache and logout
        cache.clear_cache()
        # logout_user()
        return {'success': True}
    else:
        return {
            'success': False,
            'error': res
        }


@bp.route('/backups/download/<backup_id>', methods=['GET'])
@login_required
def download_backup(backup_id):
    full_path = backups.backup_file_name(backup_id)
    if full_path is None:
        abort(404)

    headers = []
    content_length = os.path.getsize(full_path)
    headers.append(('Content-Length', str(content_length)))
    headers.append(('Content-Disposition', str('attachment; filename={0}'.format(filename))))

    response = Response(content_type='application/octet-stream')
    try:
        response.app_iter = open(full_path, 'rb')
    except IOError:
        abort(404)

    response.headerlist += headers

    return response

@bp.route('/backups/delete', methods=['POST'])
@login_required
def delete_backups_ajax():
    return {}