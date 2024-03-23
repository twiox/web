from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    return dictionary.get(key, None)


@register.filter
def isin(item, collection):
    return item in collection


@register.filter
def multiply(value, factor):
    return value * factor


@register.filter
def substract(val1, val2):
    return val1 - val2
