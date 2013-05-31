# -*- coding: utf-8 -*-
from digipal.models import *
import re
from django import http, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _ 
from django.utils.safestring import mark_safe
import htmlentitydefs
from django.db.models import Q

from django.http import HttpResponse, Http404

import logging
from django.utils.datastructures import SortedDict
dplog = logging.getLogger( 'digipal_debugger')

@staff_member_required
def stewart_import(request, url=None):
    context = {}
    record_ids = request.GET.get('ids', '').split(',')
    context['records'] = StewartRecord.objects.filter(id__in=record_ids)
    
    for record in context['records']:
        record.import_steward_record()
            
    from django.shortcuts import render
    return render(request, 'admin/stewartrecord/import.html', context)

@staff_member_required
def stewart_match(request, url=None):
    context = {}
    record_ids = request.GET.get('ids', '').split(',')
    context['records'] = StewartRecord.objects.filter(id__in=record_ids)
    
    action = request.POST.get('action', '').strip()
        
    default_hand = Hand(label='No matching hand')

    for record in context['records']:
        if action == 'change_matching':
            new_id = int(request.POST.get('shand_%s' % record.id, '0').strip())
            if new_id == 0: new_id = None
            record.hand_id = new_id 
            record.save()
        
        record.dhands = get_best_matches(record)
        record.dhands.insert(0, default_hand)
        record.hands_count = len(record.dhands) - 1
            
    #return view_utils.get_template('admin/editions/folio_image/bulk_edit', context, request)
    from django.shortcuts import render
    return render(request, 'admin/stewartrecord/match.html', context)

def add_matching_hand_to_result(result, steward_record, hand, reason, highlight=False):
    reasons = ''
    hand = result.get(hand.id, hand)
    hand.match_reason = getattr(hand, 'match_reason', '') + reason
    if highlight:
        hand.highlighted = highlight
    elif steward_record.locus and hand.label and re.search(ur'\W%s\W' % steward_record.locus.replace(u'\u2013', u'-'), hand.label.replace(u'\u2013', u'-')): 
        hand.highlighted = True
    elif steward_record.locus and hand.description and re.search(ur'\W%s\W' % steward_record.locus.replace(u'\u2013', u'-'), hand.description.replace(u'\u2013', u'-')): 
        hand.highlighted = True
    result[hand.id] = hand

def get_best_matches(record):
    ret = SortedDict()
    
    record.documents = {}
    
    # Match based on legacy id (record.stokes_db)
    hand_id = record.stokes_db.strip()
    if hand_id:
        hands = Hand.objects.filter(legacy_id=hand_id)
        for hand in hands:
            add_matching_hand_to_result(ret, record, hand, 'L', True)
        
    # Match based on K ids
    sources = ['ker', 'gneuss', 'scragg', 'sp']
    for source in sources:
        document_id = getattr(record, source, '').strip()
        if document_id:
            source_dp = source
            if source == 'sp':
                source_dp = 'sawyer'
                document_id_p = re.sub('(?i)^\s*p\s*(\d+)', r'\1', document_id)
                if document_id_p != document_id: 
                    document_id = document_id_p
                    source_dp = 'pelteret'
            document_ids = re.split('\s*,\s*', document_id)
            documents = ItemPart.objects.filter(historical_item__catalogue_numbers__source__name=source_dp,
                                                historical_item__catalogue_numbers__number__in=document_ids).distinct()
            for doc in documents: record.documents[doc.id] = doc
            hands = Hand.objects.filter(Q(pages__item_part__in=documents) | Q(item_part__in=documents)).order_by('id')
            for hand in hands:
                add_matching_hand_to_result(ret, record, hand, source.upper()[0])
            
    # find best matches based on the historical item
    
    # Existing match (record.hand)
    if record.hand:
        add_matching_hand_to_result(ret, record, record.hand, 'M')
    
    record.documents = record.documents.values()
    
    return [h for h in ret.values()]
