import uuid
from time import time

from app.extensions import db

class File(db.Model):
    __tablename__ = 'pbstoragefile'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), unique=True)
    content_type = db.Column(db.String(50))
    size = db.Column(db.Integer)
    dltype = db.Column(db.String(10))  # "download"|"auto"
    etag = db.Column(db.String(50))
    updated = db.Column(db.Integer)

    def __init__(self):
        self.etag = str(uuid.uuid4())
        self.dltype = 'auto'
        self.updated = int(time())

allowed_dltypes = ('auto', 'download')

# _storage_directory = False


# def get_storage_dirs():
#     # create if required
#     if not os.path.exists(_storage_directory):
#         os.mkdir(_storage_directory)

#     subdirs = ('orig', 'img_preview_mid')
#     res = {}
#     for s in subdirs:
#         path = os.path.join(_storage_directory, s)
#         res[s] = path
#         if not os.path.exists(path):
#             os.mkdir(path)

#     # TODO: also check that dir is a really dir

#     return res


# def get_backups_dir():
#     backups_dir = os.path.join(_storage_directory, 'backups')

#     if not os.path.exists(_storage_directory):
#         os.mkdir(_storage_directory)

#     if not os.path.exists(backups_dir):
#         os.mkdir(backups_dir)

#     return backups_dir


# def init_storage_from_settings(settings):
#     global _storage_directory
#     # init storage directory settings['pyrone.storage_directory']
#     _storage_directory = settings['pyrone.storage_directory']
#     get_storage_dirs()
#     get_backups_dir()