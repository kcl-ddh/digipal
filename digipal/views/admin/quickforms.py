# -*- coding: utf-8 -*-
import re
from django import http, template
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from digipal.views.content_type.search_content_type import get_form_field_from_queryset

from django import forms
from digipal.models import HistoricalItem, CurrentItem, Repository, Place

from digipal.utils import sorted_natural
class NewItemPartForm(forms.Form):
    
#     historical_item = get_form_field_from_queryset(HistoricalItem.objects.all(), 'New Historical Item', is_key_id=True)
#     current_item = get_form_field_from_queryset(CurrentItem.objects.all(), 'New shelfmark', is_key_id=True)
#     repo = get_form_field_from_queryset(Repository.objects.all(), 'New repository', is_key_id=True)
#     repo_place = get_form_field_from_queryset(Place.objects.all(), 'New place', is_key_id=True)

    shelfmark = forms.CharField(max_length=64)
    repository = forms.CharField(max_length=64)

    locus = forms.CharField(max_length=64)

    cat_num = forms.CharField(max_length=64)
    name = forms.CharField(max_length=64)

@staff_member_required
def add_itempart_view(request):
    from digipal.models import ItemPart, HistoricalItem, CurrentItem, Repository, Place, ItemPartItem
    
    fieldset = [
                 ['Current Item', 
                    {'key': 'shelfmark', 'label': 'Shelfmark', 'required': True},
                    {'key': 'repository', 'label': 'Repository', 'required': True},
                ],
                 ['Locus', 
                    {'key': 'locus', 'label': 'Locus'},
                ],
                 ['Historical Item',
                    {'key': 'cat_num', 'label': 'Catalogue Number'},
                    {'key': 'hi_name', 'label': 'Name', 'list': [hi.name for hi in HistoricalItem.objects.all()]},
                ]
            ]
    
    context = {'form': fieldset}
    
    import json
    from digipal.utils import sorted_natural
    for group in fieldset:
        for field in group:
            if isinstance(field, dict):
                if 'list' in field:
                    field['list_json'] = json.dumps(sorted_natural(list(set([n for n in field['list'] if n]))))
                    print field['list_json']
    
    if request.method == "POST":
        # current item
        current_item = None
        #current_item = CurrentItem.get_or_create(shelfmark=request.REQUEST.get('shelfmark', ''), repository=request.REQUEST.get('repository', ''))

        # create the new records
        itempart = ItemPart(locus=request.REQUEST.get('locus', ''), current_item=current_item)

        itempart.save()

        # historical item
        historical_item = HistoricalItem.get_or_create(name=request.REQUEST.get('hi_name', ''), cat_num=request.REQUEST.get('cat_num', ''))
        
        if historical_item:
            # item part
            ItemPartItem(item_part=itempart, historical_item=historical_item).save()
        
        # TODO: redirect to the edit form
        # TODO: add a confirmation message
        pass        

    return render(request, 'admin/digipal/add_itempart.html', context)

 