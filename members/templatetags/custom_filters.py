from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    return dictionary.get(key, None)


@register.filter
def isin(item, collection):
    return item in collection
