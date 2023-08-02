import os

from base64 import b64encode, b64decode


STORAGE_PATH = None
BACKUPS_PATH = None


def init_app(app):
    global STORAGE_PATH, BACKUPS_PATH
    STORAGE_PATH = app.config.get('PYRENGINE_STORAGE_PATH')
    BACKUPS_PATH = os.path.join(STORAGE_PATH, 'backups')
    if not os.path.exists(BACKUPS_PATH):
        os.mkdir(BACKUPS_PATH)


def list_backups():
    items = []
    for ind, fn in enumerate(os.listdir(BACKUPS_PATH), 1):
        full_fn = os.path.join(BACKUPS_PATH, fn)
        if not os.path.isfile(full_fn):
            continue
        if not fn.endswith('.zip'):
            continue
        b = {
            'id': ind,
            'filename': fn,
            'filename_b64': b64encode(fn.encode('utf-8')).decode('utf-8'),
            'size': os.path.getsize(full_fn)
        }
        items.append(b)
    return items


def backup_file_name(backup_id):
    encoded_filename = backup_id

    headers = []

    try:
        filename = b64decode(encoded_filename).decode('utf-8')
    except TypeError:
        return None

    all_backups = [x for x in os.listdir(BACKUPS_PATH) if os.path.isfile(os.path.join(BACKUPS_PATH, x))]
    if filename not in all_backups:
        return None

    full_path = os.path.join(BACKUPS_PATH, filename)
    if not os.path.isfile(full_path):
        return None

    return full_path