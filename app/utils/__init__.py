"""
Module for helper/utilities functions
"""
import hashlib
import random
import pytz
import datetime
import calendar

from flask import url_for

CHAR_SAMPLE = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def sha3_224(s: str) -> str:
    return hashlib.sha3_224(s.encode('utf-8')).hexdigest()

def sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def hash_password(password: str) -> str:
    salt = ''.join([random.choice(CHAR_SAMPLE) for x in range(8)])
    return salt + sha3_224(salt + sha3_224(password))


def check_hashed_password(password: str, hashed_password: str) -> bool:
    print(len(hashed_password))
    if len(hashed_password) == 48:
        # assuming it's sha1 with salt from restored version
        salt = hashed_password[:8]
        return hashed_password == (salt + sha1(salt + sha1(password)))
    else:
        salt = hashed_password[:8]
        return hashed_password == (salt + sha3_224(salt + sha3_224(password)))


from app.models.config import get as get_config
def timestamp_to_str(ts, fmt='%Y-%m-%d %H:%M'):
    """
    Convert UTC seconds to time string in local timezone
    """
    tz = get_config('timezone')
    tts = datetime.datetime.utcfromtimestamp(ts)  # seconds -> time_struct
    utc_dt = pytz.utc.localize(tts).astimezone(tz)  # utc time -> local time

    t_str = utc_dt.strftime(fmt)

    return t_str


def timestamp_to_dt(ts):
    """
    Convert UTC seconds to datetime object
    """
    tz = get_config('timezone')
    tts = datetime.datetime.utcfromtimestamp(ts)  # seconds -> time_struct
    utc_dt = pytz.utc.localize(tts).astimezone(tz)  # utc time -> local time
    return utc_dt


def dt_to_timestamp(dt):
    """
    Convert datetime (UTC) object to UTC seconds
    """
    return calendar.timegm(dt.timetuple())    


def str_to_timestamp(t_str):
    """
    Convert time string in local timezone to UTC seconds
    """
    tz = get_config('timezone')
    dt = datetime.datetime.strptime(t_str, '%Y-%m-%d %H:%M')
    dt_loc = tz.localize(dt)
    dt_utc = dt_loc.astimezone(pytz.utc)

    return calendar.timegm(dt_utc.timetuple())


def user_has_permission(user, p):
    if p == 'editor' and user.is_authenticated:
        return True

    if p == 'admin' and user.is_authenticated:
        return True

    return False


def article_url(article):
    return url_for('blog.view_article', shortcut_date=article.shortcut_date, shortcut=article.shortcut)


def normalize_email(email):
    return email
