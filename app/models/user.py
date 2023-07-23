import uuid
import hashlib

from app.extensions import db
from app.utils import sha3_224

class User(db.Model):
    __tablename__ = 'pbuser'

    _str_roles = None

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255))
    password = db.Column(db.String(255))
    display_name = db.Column(db.Unicode(255))
    email = db.Column(db.Unicode(255))
    # user kind (class, type), possible values: "local", "twitter"
    kind = db.Column(db.String(20))

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.login

    def is_active(self):
        return True

    # roles = db.relationship('Role')

    # def detach(self):
    #     dbsession = Session.object_session(self)
    #     if dbsession is None:
    #         return

    #     for x in self.roles:
    #         dbsession.expunge(x)

    #     dbsession.expunge(self)

    # def has_role(self, r):
    #     return r in self.get_roles()

    # def get_roles(self):
    #     if self._str_roles is None:
    #         self._str_roles = [x.name for x in self.roles]

    #     return self._str_roles


class AnonymousUser:
    kind = 'anonymous'

    def is_authenticated(self):
        return False

    def is_anonymous(self):
        return True

    def get_id(self):
        return 'anonymous'

    def is_active(self):
        return True

# anonymous = AnonymousUser()


# class Role(db.Model):
#     __tablename__ = 'pbuserrole'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('pbuser.id'))
#     name = db.Column(db.String(50))

#     def __init__(self, id, user_id, name):
#         self.id = id
#         self.user_id = user_id
#         self.name = name


# class VerifiedEmail(db.Model):
#     __tablename__ = 'pbverifiedemail'

#     # stripperd lowcased email address
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.Unicode(255), unique=True)
#     is_verified = db.Column(db.Boolean)
#     last_verify_date = db.Column(db.Integer)
#     verification_code = db.Column(db.String(255))

#     def __init__(self, email):
#         self.last_verify_date = int(time())
#         self.email = email
#         self.is_verified = False
#         self.verification_code = str(uuid.uuid4())


# def find_local_user(login, password):
#     hashed_password = md5(password)
#     dbsession = DBSession()
#     q = dbsession.query(User).options(joinedload('roles')).filter(User.kind == 'local').\
#         filter(User.login == login)
#     user = q.first()

#     if user is None:
#         return None

#     if user.password == hashed_password:
#         # old password hashing method is used
#         return user
#     else:
#         # possibly a new method is used
#         salt = user.password[:8].encode('utf8')
#         hashed_password = salt + sha1(salt + sha1(password.encode('utf8')))
#         print((user.password, hashed_password, type(user.password), type(hashed_password)))
#         if user.password == hashed_password.decode('utf8'):
#             return user

#     return None


# def normalize_email(email):
#     return email


# def get_user(user_id):
#     dbsession = DBSession()
#     user = dbsession.query(User).options(joinedload('roles')).get(user_id)
#     return user


# def find_twitter_user(username):
#     dbsession = DBSession()
#     q = dbsession.query(User).options(joinedload('roles')).filter(User.kind == 'twitter').\
#         filter(User.login == username)
#     user = q.first()
#     return user