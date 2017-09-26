from django.template import Library
from digipal.models import Image
from django.db.models import Q
import json


register = Library()


@register.inclusion_tag('sections/pages.html', takes_context=True)
def pages(context):
    list_manuscripts = []
    pages = Image.objects.values('item_part__current_item__repository__name',
                                 'item_part__current_item__repository__place__name').distinct()
    for page in pages:
        list_manuscripts.append(
            page['item_part__current_item__repository__name'])
        list_manuscripts.append(
            page['item_part__current_item__repository__place__name'])
    list_manuscripts = set(list_manuscripts)
    return {'pages': json.dumps(list(list_manuscripts))}
