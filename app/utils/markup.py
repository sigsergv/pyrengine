"""
Contains function for supported text markupt languages
"""
import markdown
import re
import logging
import hashlib

from app.utils.md_subscript import SubscriptExtension

log = logging.getLogger(__name__)

def slugify(value, separator):
    return hashlib.md5(value.encode('utf-8')).hexdigest()
    
MARKUP_CONTINUE_MARKER = "<cut>"


def render_text_markup_mini(text):
    """
    Render text using reduced markup elements set
    """
    md_mini = markdown.Markdown(safe_mode=True, enable_attributes=True, output_format='html')
    return md_mini.convert(text)


def render_text_markup(text):
    """
    render article text, return tuple (html_preview, html_body)
    """
    md = markdown.Markdown(
        extensions=['footnotes', 'wikilinks', 'def_list', 'toc', 'legacy_attrs',
        'codehilite', 'fenced_code', SubscriptExtension()],
        extension_configs={
            'codehilite': {'guess_lang':False},
            #'footnotes': [("PLACE_MARKER", "~~~~~~~~")]
            'toc': {
                'slugify': slugify,
                'permalink': '¶' # ⚓︎
            }
        },
        safe_mode=True,
        enable_attributes=True,
        output_format='html5')

    text = pre_render_text_markup(text)
    ind = text.find(MARKUP_CONTINUE_MARKER)
    if ind != -1:
        preview_part = text[:ind]
        complete_text = text.replace(MARKUP_CONTINUE_MARKER, "", 1)
    else:
        preview_part = None
        complete_text = text

    preview_html = None
    if preview_part is not None:
        # remove footnotes from the preview
        preview_part = re.sub('\\[\\^[^\\]]+?\\]', '', preview_part)
        # log.debug(preview_part)
        preview_html = md.convert(preview_part)

    complete_html = md.convert(complete_text)

    return (preview_html, complete_html)

storage_img_re = False
storage_img_preview_re = False


def pre_render_text_markup(text):
    """
    Render links to files from the storage including inline pictures from the files storage
    """
    global storage_img_re, storage_img_preview_re

    if storage_img_preview_re is False:
        storage_img_preview_re = re.compile("!(!\[[^\]]+\])\(([^)]+)/m\)")

    if storage_img_re is False:
        storage_img_re = re.compile("!(!\[[^\]]+\])\(([^)]+)\)")

    # replace preview images
    text = storage_img_preview_re.sub("[\\1(/files/p/\\2)](/files/f/\\2)", text)

    # replace constructions "!![Alt text](IMGID)" with "![Alt text](/storage/f/IMGID)"
    text = storage_img_re.sub("\\1(/files/f/\\2)", text)
    return text
