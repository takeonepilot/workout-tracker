# apps/workout/templatetags/custom_filters.py

from django import template

register = template.Library()


@register.filter
def get_item_at_index(lst, index):
    try:
        return lst[index]
    except IndexError:
        return None
