from django import template
from django.conf import settings

register = template.Library()

@register.tag
def value_from_settings(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, var = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return ValueFromSettings(tag_name, var)

class ValueFromSettings(template.Node):
    def __init__(self, tag_name, var):
        self.argname = tag_name
        self.arg = template.Variable(var)
    def render(self, context):        
        attr = getattr(settings, str(self.arg), "")
        context[str(self.arg)] = attr
        return ''
