import os

from mimetypes import guess_type
from datetime import datetime

from flask import (render_template, abort, request, redirect, url_for)
from werkzeug.utils import secure_filename
from pyrengine import (backups, files, jinja_helpers)
from pyrengine.admin import bp
from pyrengine.models import (File, Config)
from pyrengine.models.config import set as set_config
from pyrengine.models.config import get as get_config
from pyrengine.utils import cache, dt_to_timestamp
from pyrengine.files import FILES_PATH

from pyrengine.extensions import db

from flask_login import (login_user, logout_user, login_required, current_user)

@bp.route('/')
@login_required
def index():
    return 'ADMIN AREA'

@bp.route('/files')
@login_required
def files_list():
    ctx = {
    }
    dbsession = db.session
    ctx['files'] = dbsession.query(File).all()

    return render_template('admin/files_list.jinja2', **ctx)


@bp.route('/files/upload', methods=['POST'])
@login_required
def upload_file():
    form = request.form
    if 'filedata' not in request.files:
        abort(400, 'Missing filedata in POST query.')
    file = request.files['filedata']
    if file.filename == '':
        abort(400, 'Missing filename')
    filename = secure_filename(file.filename)
    storage_file = os.path.join(FILES_PATH, filename)
    file.save(storage_file)

    # save to database first
    content_type = guess_type(filename)[0] or 'application/octet-stream'
    now = datetime.utcnow()
    dbsession = db.session
    dbfile = dbsession.query(File).filter(File.name==filename).first()
    if dbfile is None:
        dbfile = File()
    dbfile.name = filename
    dbfile.size = os.stat(storage_file).st_size
    dbfile.dltype = 'download' if request.form.get('dltype', 'auto') == 'download' else 'auto'
    dbfile.content_type = content_type
    dbfile.updated = dt_to_timestamp(now)
    dbsession.add(dbfile)
    dbsession.commit()
    return redirect(url_for('admin.files_list'))


@bp.route('/files/upload/check', methods=['POST'])
@login_required
def upload_file_check_ajax():
    return {}


@bp.route('/files/<int:file_id>/edit/check', methods=['POST'])
@login_required
def edit_file_props_check_ajax():
    return {}


@bp.route('/files/<int:file_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_file_props(file_id):
    dbsession = db.session
    f = dbsession.query(File).get(file_id)
    if f is None:
        abort(404)

    ctx = {
        'file': f,
        'errors': {}
    }

    if request.method == 'GET':
        return render_template('admin/edit_file_props.jinja2', **ctx)
    else:
        f.name = secure_filename(request.form['filename'])
        f.dltype = request.form['dltype']
        f.content_type = request.form['content_type']
        dbsession.commit()
        return redirect(url_for('admin.files_list'))


@bp.route('/files/delete', methods=['POST'])
@login_required
def delete_files_ajax():
    dbsession = db.session
    jctx = {
        'success': True,
        'deleted': []
    }
    try:
        uids = [int(x) for x in request.form.get('uids', '').split(',')]
    except Exception:
        jctx['success'] = False
        jctx['error'] = _('Invalid input data')
    filenames = []
    for file_id in uids:
        file = dbsession.query(File).get(file_id)
        if file is not None:
            filenames.append(file.name)
            dbsession.delete(file)
            jctx['deleted'].append(file_id)
    dbsession.commit()
    for fn in filenames:
        os.unlink(os.path.join(FILES_PATH, fn))
    return jctx


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


@bp.route('/settings')
@login_required
def settings():
    ctx = {
        'settings': {},
        'errors': {}
    }
    dbsession = db.session
    for c in dbsession.query(Config).all():
        ctx['settings'][c.id] = c.value

    return render_template('admin/settings.jinja2', **ctx)


@bp.route('/settings/save', methods=['POST'])
@login_required
def settings_save_ajax():
    dbsession = db.session
    settings = ('site_title', 'site_base_url', 'site_copyright', 'elements_on_page',
        'admin_notifications_email', 'notifications_from_email',
        'image_preview_width', 'google_analytics_id', 'timezone', 'ui_lang', 
        'site_search_widget_code', 'ui_theme')
    for name in settings:
        c = dbsession.query(Config).get(name)
        if c is None:
            continue
        v = request.form.get(name, None)
        if v is not None:
            c.value = v
            dbsession.add(c)
    bool_settings = ('admin_notify_new_comments', 'admin_notify_new_user')
    for name in bool_settings:
        c = dbsession.query(Config).get(name)
        if c is None:
            continue
        v = request.form.get(name, None)
        if v is not None:
            c.value = ('true' if v == 'true' else 'false')
            dbsession.add(c)
    dbsession.commit()
    cache.clear_cache()
    return {}


@bp.route('/settings/widget/pages')
@login_required
def settings_widget_pages():
    ctx = {
        'widget_pages_pages_spec': get_config('widget_pages_pages_spec'),
        'errors': {}
    }
    return render_template('admin/settings_pages_widget.jinja2', **ctx)

@bp.route('/settings/widget/pages/save', methods=['POST'])
@login_required
def settings_widget_pages_save_ajax():
    # dbsession = db.session
    widget_pages_pages_spec = request.form.get('widget_pages_pages_spec', '')
    set_config('widget_pages_pages_spec', widget_pages_pages_spec)
    jinja_helpers.get_pages_widget_links(True)
    return {}
