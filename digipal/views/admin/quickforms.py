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


@staff_member_required
def add_itempart_view(request):
    from digipal.models import ItemPart, HistoricalItem, CurrentItem, Repository, Place, ItemPartItem, CatalogueNumber

    fieldset = [
        ['Current Item',
         {'key': 'shelfmark', 'label': 'Shelfmark', 'required': True, 'list': [
             ci.shelfmark for ci in CurrentItem.objects.all()], 'eg': 'Cotton Domitian vii'},
         {'key': 'repository', 'label': 'Repository', 'required': True, 'list': [u'%s, %s' % (
             repo.place, repo.name) for repo in Repository.objects.all()], 'eg': 'London, British Library'},
         ],
        ['Item Part',
         {'key': 'locus', 'label': 'Locus', 'eg': 'fols. 15–45'},
         ],
        ['Historical Item',
         {'key': 'cat_num', 'label': 'Catalogue Number', 'list': [
             unicode(cn) for cn in CatalogueNumber.objects.all()], 'eg': 'K. 190'},
         {'key': 'hi_name', 'label': 'Name', 'list': [
             hi.name for hi in HistoricalItem.objects.all()], 'eg': 'Durham Liber Vitae'},
         ]
    ]

    context = {'form': fieldset, 'title': 'Add Item Part'}

    import json
    from digipal.utils import sorted_natural
    for group in fieldset:
        for field in group:
            if isinstance(field, dict):
                if 'list' in field:
                    field['list_json'] = json.dumps(sorted_natural(
                        list(set([n for n in field['list'] if n])), True))

    if request.method == "POST":
        # current item
        current_item = CurrentItem.get_or_create(shelfmark=request.POST.get(
            'shelfmark', ''), repository=request.POST.get('repository', ''))

        # create the new records
        itempart = ItemPart(locus=request.POST.get(
            'locus', ''), current_item=current_item)

        itempart.save()

        # historical item
        historical_item = HistoricalItem.get_or_create(name=request.POST.get(
            'hi_name', ''), cat_num=request.POST.get('cat_num', ''))

        if historical_item:
            # item part
            ItemPartItem(item_part=itempart,
                         historical_item=historical_item).save()

        # add a confirmation message
        from django.contrib import messages
        messages.add_message(request, messages.SUCCESS,
                             'The item part was added successfully. You may edit it again below.')

        # redirect to the edit form
        from django.http import HttpResponseRedirect
        from django.core.urlresolvers import reverse
        return HttpResponseRedirect(reverse('admin:digipal_itempart_change', args=(itempart.id,)))

        pass

    return render(request, 'admin/digipal/add_itempart.html', context)
