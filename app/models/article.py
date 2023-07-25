from time import time
from app.extensions import db
from app.utils import markup

from .user import User

class Article(db.Model):
    __tablename__ = 'pbarticle'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    shortcut_date = db.Column(db.Unicode(50))  # somethig like "2011/03/29"
    shortcut = db.Column(db.Unicode(255))  # something like "test-post-subject"
    title = db.Column(db.Unicode(255))
    body = db.Column(db.UnicodeText())
    rendered_preview = db.Column(db.UnicodeText())
    rendered_body = db.Column(db.UnicodeText())
    # UTC timestamp of publishing
    published = db.Column(db.Integer)
    # UTC timestamp of article update
    updated = db.Column(db.Integer)
    # cached comments number
    comments_total = db.Column(db.Integer, default=0)
    comments_approved = db.Column(db.Integer, default=0)
    is_commentable = db.Column(db.Boolean, default=False)
    is_draft = db.Column(db.Boolean, default=True)
    is_splitted = db.Column(db.Boolean, default=False)

    comments = db.relationship('Comment', back_populates='article')
    user = db.relationship('User')
    tags = db.relationship('Tag')

    # def __init__(self, shortcut='', title='', is_draft=True, is_commentable=True):
    #     self.shortcut = shortcut
    #     self.title = title
    #     self.is_commentable = is_commentable
    #     self.is_draft = is_draft

    #     self.published = int(time())  # UTC time
    #     self.updated = int(time())  # UTC time
    
    def set_body(self, body):
        """
        Set article body: parse, render, split into preview and complete parts etc
        """
        self.body = body
        preview, complete = markup.render_text_markup(body)
        self.rendered_preview = preview
        self.rendered_body = complete
        self.is_splitted = preview is not None

    def get_html_preview(self):
        if self.rendered_preview is None:
            return self.rendered_body
        else:
            return self.rendered_preview


class Tag(db.Model):
    __tablename__ = 'pbtag'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey(Article.id))
    tag = db.Column(db.Unicode(255))

    # we don't need explict reference to article

    def __init__(self, name, article):
        self.tag = name
        self.article_id = article.id


class Comment(db.Model):
    __tablename__ = 'pbarticlecomment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    article_id = db.Column(db.Integer, db.ForeignKey(Article.id))
    parent_id = db.Column(db.Integer, db.ForeignKey('pbarticlecomment.id', ondelete='CASCADE'),)
    display_name = db.Column(db.Unicode(255))
    email = db.Column(db.Unicode(255))
    website = db.Column(db.Unicode(255))
    body = db.Column(db.UnicodeText)
    rendered_body = db.Column(db.UnicodeText)
    published = db.Column(db.Integer)
    ip_address = db.Column(db.String(30))
    xff_ip_address = db.Column(db.String(30))
    is_approved = db.Column(db.Boolean, default=False)
    # uf True then all answers to this comment will be send to email
    is_subscribed = db.Column(db.Boolean, default=False)

    article = db.relationship('Article', back_populates='comments')
    user = db.relationship('User')
    ## parent = relationship('Comment', remote_side=[id])
    children = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan', passive_deletes=True)

    # def set_body(self, body):
    #     """
    #     Set comment body
    #     """
    #     self.body = body
    #     self.rendered_body = markup.render_text_markup_mini(body)

    def __init__(self):
        # self.user_id = None
        self.published = int(time())