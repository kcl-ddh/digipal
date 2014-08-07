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
from django.db import transaction

import logging
from django.utils.datastructures import SortedDict
dplog = logging.getLogger( 'digipal_debugger')

@staff_member_required
def stewart_import(request, url=None):
    context = {}
    context['ids'] = request.GET.get('ids', '')
    record_ids = context['ids'].split(',')
    context['records'] = StewartRecord.objects.filter(id__in=record_ids)
    context['dry-run'] = (request.GET.get('dry-run', '0') == '1')
    
    class RollBackException(Exception):
        pass
    
    try:
        with transaction.atomic():
            for record in context['records']:
                record.import_steward_record()
            if context['dry-run']:
                raise RollBackException()
    except RollBackException:
        context['rolledback'] = True
        pass
            
    from django.shortcuts import render
    return render(request, 'admin/stewartrecord/import.html', context)

def get_new_hand_from_stewart_record(record, item_part_id=0):
    if not item_part_id: return None
    ret = Hand(num='10000')
    ret.item_part_id = item_part_id
    ret.internal_note = (ret.internal_note or '') + '\nNew Hand created from Brookes record #%s' % record.id
    record.import_steward_record(ret)
    return ret

@staff_member_required
def stewart_match(request, url=None):
    context = {}
    record_ids = request.GET.get('ids', '').split(',')
    context['records'] = StewartRecord.objects.filter(id__in=record_ids)
    
    from django.core.urlresolvers import reverse
    context['referer'] = request.REQUEST.get('referer', request.META.get('HTTP_REFERER', reverse('admin:digipal_stewartrecord_changelist')))
    
    action = request.POST.get('action', '').strip()
        
    context['item_parts'] = ItemPart.objects.all().order_by('display_label')
        
    for record in context['records']:
        
        if action == 'change_matching':
            matched_hands = []
            i = 0
            for i in range(0, int(request.REQUEST.get('shand_%s_count' % (record.id,), 0))):
                match_id = request.REQUEST.get('shand_%s_%s' % (record.id, i), None)
                if match_id: 
                    matched_hands.append(match_id)
            record.set_matched_hands(matched_hands)
            record.save()
        
        record.dhands = get_best_matches(record)

        #default_hand.selected = not any([getattr(h, 'selected', False) for h in record.dhands])
        #record.dhands.insert(0, default_hand)
        
#     <select name="shand_{{ record.id }}_item_part">
#         {% for item in item_parts %}

    #return view_utils.get_template('admin/editions/folio_image/bulk_edit', context, request)
    from django.shortcuts import render
    return render(request, 'admin/stewartrecord/match.html', context)

def add_matching_hand_to_result(result, steward_record, hand, reason, highlight=False):
    hand = result.get(hand.id, hand)
    hand.match_reason = getattr(hand, 'match_reason', '') + reason
    if highlight:
        hand.highlighted = highlight
    if steward_record.locus:
        locus = steward_record.locus.replace(u'\u2013', u'-').strip('[] ')
        if hand.label and re.search(ur'(?i)\W%s\W' % re.escape(locus), hand.label.replace(u'\u2013', u'-')): 
            hand.highlighted = True
        if hand.description and re.search(ur'(?i)\W%s\W' % re.escape(locus), hand.description.replace(u'\u2013', u'-')): 
            hand.highlighted = True
    
    hand.match_id = u'h:%s' % hand.id
    hand.selected = hand.match_id in steward_record.get_matched_hands()
    
    result[hand.id] = hand
    if hand.num == 10000: hand.isnew = True
    
    return hand

def get_best_matches(record):
    ret = SortedDict()
    
    record.documents = {}
    
    # Match based on legacy id (record.stokes_db)
    hand_id = record.stokes_db.strip()
    if hand_id:
        hands = Hand.objects.filter(legacy_id=hand_id)
        for hand in hands:
            add_matching_hand_to_result(ret, record, hand, 'L', True)

    # Match based on scragg id (record.scragg, hand.scragg)
    hand_id = record.scragg.strip()
    if hand_id:
        hands = Hand.objects.filter(scragg=hand_id)
        for hand in hands:
            add_matching_hand_to_result(ret, record, hand, 'Scr', False)
        
    # Match based on K/G/S/P ids
    sources = ['ker', 'gneuss', 'sp']
    for source in sources:
        document_id = getattr(record, source, '').strip()
        if document_id:
            source_dp = source
            if source == 'sp':
                source_dp = settings.SOURCE_SAWYER_KW
                document_id_p = re.sub('(?i)^\s*p\s*(\d+)', r'\1', document_id)
                source = 'S'
                if document_id_p != document_id: 
                    document_id = document_id_p
                    source_dp = 'pelteret'
                    source = 'P'
            document_ids = re.split('\s*,\s*', document_id)
            documents = ItemPart.objects.filter(Q(historical_items__catalogue_numbers__source=Source.get_source_from_keyword(source_dp)) & \
                                                Q(historical_items__catalogue_numbers__number__in=document_ids)).distinct()
            for doc in documents: record.documents[doc.id] = doc
            hands = Hand.objects.filter(Q(images__item_part__in=documents) | Q(item_part__in=documents)).distinct().order_by('id')
            for hand in hands:
                add_matching_hand_to_result(ret, record, hand, source.upper()[0])
            
    # find best matches based on the historical item
    
    # Existing match (record.hand)
#     for hand in record.hands.all():
#         hand = add_matching_hand_to_result(ret, record, hand, 'M')
#         hand.selected = True
        
#     for matched_hand in record.get_matched_hands():
#         hand = None
#         if matched_hand['type'] == 'hand':
#             hand = Hand.objects.get(id=int(matched_hand['id']))
#             hand = add_matching_hand_to_result(ret, record, hand, 'M')
#         if matched_hand['type'] == 'itempart':
#             hand = add_matching_hand_to_result(ret, record, hand, 'M')
#         hand.selected = True
#         
#     # New Hand
#     add_matching_hand_to_result(ret, record, Hand(), 'New')
    
    record.documents = record.documents.values()
    
    return [h for h in ret.values()]
