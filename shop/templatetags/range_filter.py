from django import template

register = template.Library()

@register.filter
def range_filter(value):
    return range(1, value)