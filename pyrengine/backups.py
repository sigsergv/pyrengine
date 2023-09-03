import os
import zipfile
import shutil

from lxml import etree
from datetime import datetime
from base64 import b64encode, b64decode
from flask_babel import gettext as _
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from pyrengine.extensions import db
from pyrengine.files import (get_storage_dirs, ALLOWED_DLTYPES)
from pyrengine.models import (User, Article, Comment, Tag, VerifiedEmail, File, Config)

STORAGE_PATH = None
BACKUPS_PATH = None


def init(app):
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
            'id': b64encode(fn.encode('utf-8')).decode('utf-8'),
            'ind': ind,
            'filename': fn,
            'size': os.path.getsize(full_fn)
        }
        items.append(b)
    return sorted(items, key=lambda x: x['filename'])


def backup_file_name(backup_id):
    headers = []

    try:
        filename = b64decode(backup_id).decode('utf-8')
    except TypeError:
        return None

    all_backups = [x for x in os.listdir(BACKUPS_PATH) if os.path.isfile(os.path.join(BACKUPS_PATH, x))]
    if filename not in all_backups:
        return None

    full_path = os.path.join(BACKUPS_PATH, filename)
    if not os.path.isfile(full_path):
        return None

    return full_path


def delete_backup(backup_id):
    filename = backup_file_name(backup_id)
    if filename is None:
        return False
    try:
        os.unlink(filename)
    except Exception as e:
        logger.error('Failed to delete backup, error: {0}'.format(str(e)))
        return False
    return True


def restore_backup(backup_id):
    try:
        filename = b64decode(backup_id).decode('utf-8')
    except TypeError:
        return _('Backup ID cannot be processed.')

    all_backups = [x for x in os.listdir(BACKUPS_PATH) if os.path.isfile(os.path.join(BACKUPS_PATH, x))]
    if filename not in all_backups:
        return _('Backup not found.')

    full_filename = os.path.join(BACKUPS_PATH, filename)

    try:
        z = zipfile.ZipFile(full_filename)
    except zipfile.BadZipfile:
        return _('Backup file is broken!')

    # now check zip file contents, first extract file "index.xml"
    try:
        xml_f = z.open('index.xml')
    except KeyError:
        return _('Backup file is broken, no catalog file inside!')

    try:
        xmldoc = etree.parse(xml_f)
    except etree.XMLSyntaxError:
        return _('Backup file is broken, XML catalog is broken!')

    root = xmldoc.getroot()
    NS = 'http://regolit.com/ns/pyrone/backup/1.0'

    def t(name):
        """
        Convert tag name "name" to full qualified name like "{http://regolit.com/ns/pyrone/backup/1.0}name"
        """
        return '{{{0}}}{1}'.format(NS, name)

    def unt(name):
        """
        Remove namespace
        """
        return name.replace('{{{0}}}'.format(NS), '')

    # now check is backup version supported
    if root.tag != t('backup'):
        return _('Unknown XML format of catalog file.')

    backup_version = root.get('version')

    if backup_version not in ('1.1', '1.2'):
        return _('Unsupported backup version: “{0}”!'.format(root.get('version')))

    ## restore data
    dbsession = db.session
    dialect_name = dbsession.get_bind().name

    # first delete everything from database
    dbsession.query(Comment).delete()
    dbsession.query(Tag).delete()
    dbsession.query(Article).delete()
    dbsession.query(VerifiedEmail).delete()
    dbsession.query(File).delete()  # also remove files from the storage dir
    dbsession.query(Config).delete()
    dbsession.query(User).delete()

    namespaces = {'b': NS}

    # next restore config
    nodes = xmldoc.xpath('//b:backup/b:settings', namespaces=namespaces)

    if len(nodes) == 0:
        dbsession.rollback()
        return _('Backup file is broken: settings block not found')

    node = nodes[0]
    nodes = node.xpath('//b:config', namespaces=namespaces)
    for node in nodes:
        c = dbsession.query(Config).get(node.get('id'))
        if c is None:
            c = Config(node.get('id'), node.text)
            if c.id == 'ui_theme':
                c.value = 'default'
            dbsession.add(c)
        else:
            c.value = node.text

    # restore users
    nodes = xmldoc.xpath('//b:backup/b:users', namespaces=namespaces)
    if len(nodes) == 0:
        dbsession.rollback()
        return _('Backup file is broken: users block not found')

    node = nodes[0]
    nodes = node.xpath('./b:user', namespaces=namespaces)

    for node in nodes:
        u = User()
        u.id = int(node.get('id'))

        subnodes = node.xpath('./*', namespaces=namespaces)
        m = {}
        for sn in subnodes:
            m[unt(sn.tag)] = sn.text

        props = {'login': 'login', 'password': 'password', 'display-name': 'display_name',
                 'email': 'email', 'kind': 'kind'}
        for k, v in props.items():
            if k in m:
                setattr(u, v, m[k])

        dbsession.add(u)
        # ignore user roles

    # restore verified emails
    nodes = xmldoc.xpath('//b:backup/b:verified-emails', namespaces=namespaces)
    if len(nodes) != 0:
        # block is optional
        node = nodes[0]
        nodes = node.xpath('./b:email', namespaces=namespaces)
        for node in nodes:
            vf = VerifiedEmail(node.text)
            vf.last_verify_date = int(node.get('last-verification-date'))
            vf.is_verified = node.get('verified') == 'true'
            vf.verification_code = node.get('verification-code')
            dbsession.add(vf)

    # restore articles
    def recursively_restore_comments(tree, root):
        if root not in tree:
            return
        for comment in tree[root]:
            dbsession.add(comment)
        dbsession.flush()
        for comment in tree[root]:
            recursively_restore_comments(tree, comment.id)

    nodes = xmldoc.xpath('//b:backup/b:articles', namespaces=namespaces)
    if len(nodes) == 0:
        dbsession.rollback()
        return _('Backup file is broken: articles block not found')

    node = nodes[0]
    nodes = node.xpath('./b:article', namespaces=namespaces)

    for node in nodes:
        article = Article()
        article.id = int(node.get('id'))
        article.user_id = int(node.get('user-id'))

        subnodes = node.xpath('./*', namespaces=namespaces)
        m = {}
        for sn in subnodes:
            m[unt(sn.tag)] = sn.text

        props = {'title': 'title', 'body': 'body', 'shortcut': 'shortcut', 'shortcut-date': 'shortcut_date'}
        for k, v in props.items():
            if k in m:
                setattr(article, v, m[k])

        article.set_body(m['body'])

        props = {'published': 'published', 'updated': 'updated'}
        for k, v in props.items():
            if k in m:
                setattr(article, v, int(m[k]))

        props = {'is-commentable': 'is_commentable', 'is-draft': 'is_draft'}

        for k, v in props.items():
            if k in m:
                res = False
                if m[k].lower() == 'true':
                    res = True
                setattr(article, v, res)

        article.comments_total = 0
        article.comments_approved = 0

        # now restore tags
        subnodes = node.xpath('./b:tags/b:tag', namespaces=namespaces)
        tags_set = set()
        for sn in subnodes:
            tags_set.add(sn.text.strip())

        for tag_str in tags_set:
            tag = Tag(tag_str, article)
            dbsession.add(tag)

        # now process comments
        # we need to preserve comments hierarchy
        # local_comments = {}  # key is a comment ID, value - comment object
        local_parents = {}  # key is a parent-id, value is a list of child IDs

        subnodes = node.xpath('./b:comments/b:comment', namespaces=namespaces)
        for sn in subnodes:
            comment = Comment()
            comment.article_id = article.id
            comment.id = int(sn.get('id'))
            try:
                comment.parent_id = int(sn.get('parent-id'))
            except KeyError:
                pass
            except TypeError:
                pass

            try:
                comment.user_id = int(sn.get('user-id'))
            except TypeError:
                pass
            except KeyError:
                pass

            subsubnodes = sn.xpath('./*', namespaces=namespaces)
            m = {}
            for sn in subsubnodes:
                m[unt(sn.tag)] = sn.text

            props = {'display-name': 'display_name', 'email': 'email', 'website': 'website',
                     'ip-address': 'ip_address', 'xff-ip-address': 'xff_ip_address'}
            for k, v in props.items():
                if k in m:
                    setattr(comment, v, m[k])

            comment.set_body(m['body'])
            comment.published = int(m['published'])

            props = {'is-approved': 'is_approved', 'is-subscribed': 'is_subscribed'}
            for k, v in props.items():
                if k in m:
                    res = False
                    if m[k].lower() == 'true':
                        res = True
                    setattr(comment, v, res)

            article.comments_total += 1
            if comment.is_approved:
                article.comments_approved += 1

            parent_id = comment.parent_id
            if parent_id not in local_parents:
                local_parents[parent_id] = []
            local_parents[parent_id].append(comment)

        dbsession.add(article)
        dbsession.flush()
        
        recursively_restore_comments(local_parents, None)

    # process files
    nodes = xmldoc.xpath('//b:backup/b:files', namespaces=namespaces)
    if len(nodes) == 0:
        dbsession.rollback()
        return _('Backup file is broken: articles block not found')

    node = nodes[0]
    nodes = node.xpath('./b:file', namespaces=namespaces)

    storage_dirs = get_storage_dirs()
    for node in nodes:
        file = File()
        src = node.get('src')
        # read "name", "dltype", "updated", "content_type"

        subnodes = node.xpath('./*', namespaces=namespaces)
        m = {}
        for sn in subnodes:
            m[unt(sn.tag)] = sn.text

        props = {'name': 'name', 'dltype': 'dltype', 'content-type': 'content_type'}
        for k, v in props.items():
            if k in m:
                setattr(file, v, m[k])

        # check "file.name"
        if file.name == '.' or file.name == '..':
            continue
        if file.name.find('/') != -1 or file.name.find('\\') != -1:
            continue

        if file.dltype not in ALLOWED_DLTYPES:
            file.dltype = 'auto'

        # extract file from the archive, put to the storage dir, fill attribute "size"
        file_f = z.open(src)
        file_full_path = os.path.join(storage_dirs['orig'], file.name)
        file_out_f = open(file_full_path, 'wb')
        shutil.copyfileobj(file_f, file_out_f)
        file_f.close()
        file_out_f.close()
        file.size = os.path.getsize(file_full_path)

        dbsession.add(file)

    # catch IntegrityError here!
    try:
        dbsession.commit()
        
        # reset sequences
        if dialect_name == 'postgresql':
            dbsession.execute(text("SELECT setval('pbarticle_id_seq', (SELECT MAX(id) FROM pbarticle));"))
            dbsession.execute(text("SELECT setval('pbarticlecomment_id_seq', (SELECT MAX(id) FROM pbarticlecomment));"))
    except IntegrityError as e:
        print(e)
        return _('Unable to restore backup: database error, maybe your backup file is corrupted')
    except Exception as e:
        print(e)
        return _('Unable to restore backup: database error, maybe your backup file is corrupted')

    return True


def create_backup():
    now = datetime.now()
    ts = now.strftime('%Y%m%d-%H%M%S')
    backup_file_name = 'backup-{0}.zip'.format(ts)
    backup_tmp_dir = os.path.join(BACKUPS_PATH, 'tmp-{0}'.format(ts))

    def cleanup():
        shutil.rmtree(backup_tmp_dir, ignore_errors=True)

    os.mkdir(backup_tmp_dir)

    nsmap = {None: 'http://regolit.com/ns/pyrone/backup/1.0'}

    def e(parent, name, text=None):
        node = etree.SubElement(parent, name, nsmap=nsmap)
        if text is not None:
            node.text = text
        return node

    root = etree.Element('backup', nsmap=nsmap)
    root.set('version', '1.2')

    articles_el = e(root, 'articles')
    vf_el = e(root, 'verified-emails')
    files_el = e(root, 'files')
    settings_el = e(root, 'settings')
    users_el = e(root, 'users')

    dbsession = db.session

    # dump tables, create xml-file with data, dump files, pack all in the zip-file
    for article in dbsession.query(Article).all():
        article_el = e(articles_el, 'article')
        article_el.set('id', str(article.id))
        article_el.set('user-id', str(article.user_id))
        e(article_el, 'title', article.title)
        e(article_el, 'shortcut-date', article.shortcut_date)
        e(article_el, 'shortcut', article.shortcut)
        e(article_el, 'body', article.body)
        e(article_el, 'published', str(article.published))
        e(article_el, 'updated', str(article.updated))
        e(article_el, 'is-commentable', str(article.is_commentable))
        e(article_el, 'is-draft', str(article.is_draft))
        tags_el = e(article_el, 'tags')

        for t in article.tags:
            e(tags_el, 'tag', t.tag)

        comments_el = e(article_el, 'comments')

        for comment in article.comments:
            comment_el = e(comments_el, 'comment')
            comment_el.set('id', str(comment.id))
            if comment.user_id is not None:
                comment_el.set('user-id', str(comment.user_id))
            if comment.parent_id is not None:
                comment_el.set('parent-id', str(comment.parent_id))
            e(comment_el, 'body', comment.body)
            e(comment_el, 'email', comment.email)
            e(comment_el, 'display-name', comment.display_name)
            e(comment_el, 'published', str(comment.published))
            e(comment_el, 'ip-address', comment.ip_address)
            if comment.xff_ip_address is not None:
                e(comment_el, 'xff-ip-address', comment.xff_ip_address)
            e(comment_el, 'is-approved', str(comment.is_approved))

    # dump verified emails
    for vf in dbsession.query(VerifiedEmail).all():
        s = e(vf_el, 'email', vf.email)
        s.set('verified', 'true' if vf.is_verified else 'false')
        s.set('last-verification-date', str(int(vf.last_verify_date)))
        s.set('verification-code', vf.verification_code)

    # dump settings
    for setting in dbsession.query(Config).all():
        s = e(settings_el, 'config', setting.value)
        s.set('id', setting.id)

    # dump users
    for user in dbsession.query(User).all():
        user_el = e(users_el, 'user')
        user_el.set('id', str(user.id))
        e(user_el, 'login', user.login)
        e(user_el, 'password', user.password)
        e(user_el, 'display-name', user.display_name)
        e(user_el, 'email', user.email)
        e(user_el, 'kind', user.kind)

    # dump files
    ind = 1
    storage_dirs = get_storage_dirs()

    for f in dbsession.query(File).all():
        # check is file exists

        full_path = os.path.join(storage_dirs['orig'], f.name)
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            continue

        target_file = 'file{0:05}'.format(ind)
        shutil.copy(full_path, os.path.join(backup_tmp_dir, target_file))

        file_el = e(files_el, 'file')
        file_el.set('src', target_file)
        e(file_el, 'name', f.name)
        e(file_el, 'dltype', f.dltype)
        e(file_el, 'updated', str(f.updated))
        e(file_el, 'content-type', f.content_type)
        ind += 1

    # write xml
    index_xml = os.path.join(backup_tmp_dir, 'index.xml')
    out = open(index_xml, 'wb')
    etree.ElementTree(root).write(index_xml, pretty_print=True, encoding='UTF-8', xml_declaration=True)
    out.close()

    # compress directory
    z = zipfile.ZipFile(os.path.join(BACKUPS_PATH, backup_file_name), 'w')
    for fn in os.listdir(backup_tmp_dir):
        fn_full = os.path.join(backup_tmp_dir, fn)
        if not os.path.isfile(fn_full):
            continue

        z.write(fn_full, fn)
    z.close()

    # cleanup
    cleanup()

    return backup_file_name
