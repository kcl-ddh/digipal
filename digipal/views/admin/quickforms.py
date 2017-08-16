# -*- coding: utf-8 -*-
import re
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from digipal.views.content_type.search_content_type import get_form_field_from_queryset

from django import forms
from digipal.models import HistoricalItem, CurrentItem, Repository, Place,\
    CatalogueNumber
from django.db import transaction

from digipal.utils import sorted_natural


@staff_member_required
def add_itempart_view(request):
    fieldset = [
        ['Current Item',
            {
                'key': 'repository', 'label': 'Repository', 'required': True,
                'list': [u'%s, %s' % (repo.place, repo.name) for repo in Repository.objects.all()],
                'eg': 'London, British Library',
                'help_text': 'The library, archive or institution which currently preserves this item. Format: "City, Repository name"',
            },
            {
                'key': 'shelfmark', 'label': 'Shelfmark', 'required': True,
                'list': [ci.shelfmark for ci in CurrentItem.objects.all()],
                'eg': 'Cotton Domitian vii',
                'help_text': 'A short reference used by a repository to help locate the item.',
            },
         ],
        ['Item Part',
            {'key': 'locus', 'label': 'Locus',
             'eg': 'fols. 15–45',
             'help_text': 'The location of this part in the current item (e.g. a folio/page range). Leave blank if only one part in the Current Item.',
             },
         ],
        ['Historical Item',
            {
                'key': 'cat_num', 'label': 'Catalogue Number',
                'list': [unicode(cn) for cn in CatalogueNumber.objects.all()],
                'eg': 'K. 190',
                'help_text': 'Optional. A catalogue number. Format: "CA. CN", Where CA is the catalogue abbbreviation and CN the number or code  of this item in that catalogue.',
            },
            {
                'key': 'hi_name', 'label': 'Name',
                'list': [hi.name for hi in HistoricalItem.objects.all()],
                'eg': 'Durham Liber Vitae',
                'help_text': 'Optional. A common name for this Item.',
            },
         ]
    ]

    import json
    from digipal.utils import sorted_natural
    for group in fieldset:
        for field in group:
            if isinstance(field, dict):
                field['value'] = request.POST.get(field['key'], '')
                if 'list' in field:
                    field['list_json'] = json.dumps(sorted_natural(
                        list(set([n for n in field['list'] if n])), True))

    from django.contrib import messages
    if request.method == "POST":
        try:
            itempart = add_itempart(request)
        except ExceptionAddItemPart, e:
            messages.add_message(request, messages.ERROR, e.message)
        else:
            # add a confirmation message
            messages.add_message(request, messages.SUCCESS,
                                 'The item part was added successfully. You may edit it again below.')

            # redirect to the edit form
            from django.http import HttpResponseRedirect
            from django.core.urlresolvers import reverse
            return HttpResponseRedirect(reverse('admin:digipal_itempart_change', args=(itempart.id,)))

    context = {'form': fieldset, 'title': 'Add Item Part'}

    return render(request, 'admin/digipal/add_itempart.html', context)


class ExceptionAddItemPart(Exception):
    def __init__(self, message, fields=None):
        self.message = message
        self.fields = fields

    def __str__(self):
        return str(self.message)


@transaction.atomic
def add_itempart(request):
    from digipal.models import ItemPart, ItemPartItem
    # current item
    current_item = CurrentItem.get_or_create(shelfmark=request.POST.get(
        'shelfmark', ''), repository=request.POST.get('repository', ''))

    if current_item is None:
        raise ExceptionAddItemPart(
            'Please check the format of the Repository and Shelfmark fields.')

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

    return itempart
