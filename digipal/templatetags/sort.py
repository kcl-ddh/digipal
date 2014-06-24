from django import template

register = template.Library()

@register.filter(name='sort')
def sort_list(value):
	sorted_x = value.values().order_by('_order')
	return sorted_x