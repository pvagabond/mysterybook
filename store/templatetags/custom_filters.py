from django import template

register = template.Library()

@register.filter(name='to_cents')
def to_cents(val):
    return int(val * 100)

@register.filter(name='pluralize')
def pluralize(val):
    retval = ""
    if val > 1:
        retval = "s"
    return retval