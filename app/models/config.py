import pytz

from app.extensions import db
from app.utils import cache
from app.extensions import db

class Config(db.Model):
    __tablename__ = 'pbconfig'

    id = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.UnicodeText)

    def __init__(self, id, value):
        self.id = id
        self.value = value

# # config values are cached


# def get_all():
#     """
#     Fetch all config options, not cached
#     """
#     dbsession = DBSession()
#     all = dbsession.query(Config).all()
#     return all


def get(key, force=False):
    """
    Get settings value, set "force" to True to update corresponding value in the cache
    """
    value = cache.get_value(key)
    if value is None or force is True:
        dbsession = db.session
        c = dbsession.query(Config).get(key)
        if c is not None:
            v = c.value
            cache.set_value(key, v)
            value = v

    if key == 'timezone' and not isinstance(value, pytz.tzinfo.DstTzInfo):
        # convert timezone string to the timezone object
        try:
            value = pytz.timezone(value)
        except pytz.exceptions.UnknownTimeZoneError:
            value = pytz.timezone('UTC')
        cache.set_value(key, value)

    return cache.get_value(key)


def set(key, value, dbsession=None):
    is_transaction = False

    if dbsession is None:
        dbsession = db.session
        is_transaction = True
        transaction.begin()

    c = dbsession.query(Config).get(key)
    if c is None:
        c = Config(key, value)
        dbsession.add(c)
    else:
        c.value = value

    if is_transaction:
        transaction.commit()

    cache.set_value(key, value)