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
                    {'key': 'hi_name', 'label': 'Name'},
                ]
            ]
    
    context = {'form': fieldset}
    
    if request.method == "POST":
        from digipal.models import ItemPart, HistoricalItem, CurrentItem, Repository, Place
        # create the new records
        itempart = ItemPart(locus=request.REQUEST.get('locus', ''))
        itempart.save()
        # TODO: redirect to the edit form
        # TODO: add a confirmation message
        pass        

    return render(request, 'admin/digipal/add_itempart.html', context)
