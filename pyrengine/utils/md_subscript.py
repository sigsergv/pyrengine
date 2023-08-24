from markdown import Extension
from markdown.inlinepatterns import SimpleTagPattern

SUBSCRIPT_RE = r'(\~)([^\~]+)\2'

def makeExtension(*args, **kwargs):
    return SubscriptExtension(*args, **kwargs)


class SubscriptExtension(Extension):
    def extendMarkdown(self, md):
        # insert before 'not_strong' that have priority==70
        md.inlinePatterns.register(SimpleTagPattern(SUBSCRIPT_RE, 'sub'), 'sub', 69)
