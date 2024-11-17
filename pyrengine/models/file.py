import uuid
from time import time

from pyrengine.extensions import db

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
