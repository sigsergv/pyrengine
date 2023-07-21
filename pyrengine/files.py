import os

# STORAGE_PATH = None
FILES_PATH = None
PREVIEWS_PATH = None
ALLOWED_DLTYPES = ('auto', 'download')


def init(app):
    global FILES_PATH, PREVIEWS_PATH

    STORAGE_PATH = app.config.get('PYRENGINE_STORAGE_PATH')
    FILES_PATH = os.path.join(STORAGE_PATH, 'orig')
    PREVIEWS_PATH = os.path.join(STORAGE_PATH, 'img_preview_mid')

    for s in (FILES_PATH, PREVIEWS_PATH):
        if not os.path.exists(s):
            os.mkdir(s)

def get_storage_dirs():
    return {
        'orig': FILES_PATH,
        'img_preview_mid': PREVIEWS_PATH
    }
